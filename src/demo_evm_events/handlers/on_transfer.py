from decimal import Decimal

from tortoise.exceptions import DoesNotExist

from demo_evm_events import models as models
from demo_evm_events.types.eth_usdt.evm_events.transfer import Transfer
from dipdup.context import HandlerContext
from dipdup.models.evm_subsquid import SubsquidEvent


async def on_transfer(
    ctx: HandlerContext,
    event: SubsquidEvent[Transfer],
) -> None:
    amount = Decimal(event.payload.value) / (10**6)
    if not amount:
        return

    await on_balance_update(
        address=event.payload.from_,
        balance_update=-amount,
        level=event.data.level,
    )
    await on_balance_update(
        address=event.payload.to,
        balance_update=amount,
        level=event.data.level,
    )
    

async def on_balance_update(
    address: str,
    balance_update: Decimal,
    level: int,
) -> None:
    try:
        holder = await models.Holder.cached_get(pk=address)
    except DoesNotExist:
        holder = models.Holder(
            address=address,
            balance=0,
            turnover=0,
            tx_count=0,
            last_seen=None,
        )
        holder.cache()
    holder.balance += balance_update
    holder.turnover += abs(balance_update)
    holder.tx_count += 1
    holder.last_seen = level
    await holder.save()