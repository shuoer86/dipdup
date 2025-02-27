from dipdup import fields

from dipdup.models.tezos_tzkt import TzktOperationType
from dipdup.models import Model


class Operation(Model):
    hash = fields.TextField()
    level = fields.IntField()
    type = fields.EnumField(TzktOperationType)