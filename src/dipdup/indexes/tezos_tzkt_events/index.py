from contextlib import ExitStack
from typing import Any

from dipdup.config.tezos_tzkt_events import TzktEventsHandlerConfig
from dipdup.config.tezos_tzkt_events import TzktEventsHandlerConfigU
from dipdup.config.tezos_tzkt_events import TzktEventsIndexConfig
from dipdup.datasources.tezos_tzkt import TzktDatasource
from dipdup.exceptions import ConfigInitializationException
from dipdup.exceptions import FrameworkException
from dipdup.index import Index
from dipdup.indexes.tezos_tzkt_events.fetcher import EventFetcher
from dipdup.indexes.tezos_tzkt_events.matcher import match_events
from dipdup.models.tezos_tzkt import TzktEvent
from dipdup.models.tezos_tzkt import TzktEventData
from dipdup.models.tezos_tzkt import TzktMessageType
from dipdup.models.tezos_tzkt import TzktRollbackMessage
from dipdup.models.tezos_tzkt import TzktUnknownEvent
from dipdup.prometheus import Metrics

EventQueueItem = tuple[TzktEventData, ...] | TzktRollbackMessage


class TzktEventsIndex(
    Index[TzktEventsIndexConfig, EventQueueItem, TzktDatasource],
    message_type=TzktMessageType.event,
):
    def push_events(self, events: EventQueueItem) -> None:
        self.push_realtime_message(events)

    async def _process_queue(self) -> None:
        """Process WebSocket queue"""
        if self._queue:
            self._logger.debug('Processing websocket queue')
        while self._queue:
            message = self._queue.popleft()
            if isinstance(message, TzktRollbackMessage):
                await self._tzkt_rollback(message.from_level, message.to_level)
                continue

            message_level = message[0].level
            if message_level <= self.state.level:
                self._logger.debug('Skipping outdated message: %s <= %s', message_level, self.state.level)
                continue

            with ExitStack() as stack:
                if Metrics.enabled:
                    stack.enter_context(Metrics.measure_level_realtime_duration())
                await self._process_level_events(message, message_level)

    def _create_fetcher(self, first_level: int, last_level: int) -> EventFetcher:
        event_addresses = self._get_event_addresses()
        event_tags = self._get_event_tags()
        return EventFetcher(
            datasource=self._datasource,
            first_level=first_level,
            last_level=last_level,
            event_addresses=event_addresses,
            event_tags=event_tags,
        )

    async def _synchronize(self, sync_level: int) -> None:
        """Fetch operations via Fetcher and pass to message callback"""
        index_level = await self._enter_sync_state(sync_level)
        if index_level is None:
            return

        first_level = index_level + 1
        self._logger.info('Fetching contract events from level %s to %s', first_level, sync_level)
        fetcher = self._create_fetcher(first_level, sync_level)

        async for level, events in fetcher.fetch_by_level():
            with ExitStack() as stack:
                if Metrics.enabled:
                    Metrics.set_levels_to_sync(self._config.name, sync_level - level)
                    stack.enter_context(Metrics.measure_level_sync_duration())
                await self._process_level_events(events, sync_level)

        await self._exit_sync_state(sync_level)

    async def _process_level_events(
        self,
        events: tuple[TzktEventData, ...],
        sync_level: int,
    ) -> None:
        if not events:
            return

        batch_level = events[0].level
        index_level = self.state.level
        if batch_level <= index_level:
            raise FrameworkException(f'Batch level is lower than index level: {batch_level} <= {index_level}')

        self._logger.debug('Processing contract events of level %s', batch_level)
        matched_handlers = match_events(self._ctx.package, self._config.handlers, events)

        if Metrics.enabled:
            Metrics.set_index_handlers_matched(len(matched_handlers))

        # NOTE: We still need to bump index level but don't care if it will be done in existing transaction
        if not matched_handlers:
            await self._update_state(level=batch_level)
            return

        async with self._ctx.transactions.in_transaction(batch_level, sync_level, self.name):
            for handler_config, event in matched_handlers:
                await self._call_matched_handler(handler_config, event)
            await self._update_state(level=batch_level)

    async def _call_matched_handler(
        self, handler_config: TzktEventsHandlerConfigU, event: TzktEvent[Any] | TzktUnknownEvent
    ) -> None:
        if isinstance(handler_config, TzktEventsHandlerConfig) != isinstance(event, TzktEvent):
            raise FrameworkException(f'Invalid handler config and event types: {handler_config}, {event}')

        if not handler_config.parent:
            raise ConfigInitializationException

        await self._ctx.fire_handler(
            handler_config.callback,
            handler_config.parent.name,
            self.datasource,
            str(event.data.transaction_id),
            event,
        )

    def _get_event_addresses(self) -> set[str]:
        """Get addresses to fetch events during initial synchronization"""
        addresses = set()
        for handler_config in self._config.handlers:
            addresses.add(handler_config.contract.get_address())
        return addresses

    def _get_event_tags(self) -> set[str]:
        """Get tags to fetch events during initial synchronization"""
        paths = set()
        for handler_config in self._config.handlers:
            if isinstance(handler_config, TzktEventsHandlerConfig):
                paths.add(handler_config.tag)
        return paths
