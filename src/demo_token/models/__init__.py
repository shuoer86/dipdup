from dipdup import fields

from dipdup.models import Model


class Holder(Model):
    address = fields.TextField(pk=True)
    balance = fields.DecimalField(decimal_places=8, max_digits=20, default=0)
    turnover = fields.DecimalField(decimal_places=8, max_digits=20, default=0)
    tx_count = fields.BigIntField(default=0)
    last_seen = fields.DatetimeField(null=True)