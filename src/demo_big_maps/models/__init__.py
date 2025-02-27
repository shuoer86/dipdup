
from dipdup import fields

from dipdup.models import Model


class TLD(Model):
    id = fields.TextField(pk=True)
    owner = fields.TextField()


class Expiry(Model):
    id = fields.TextField(pk=True)
    timestamp = fields.DatetimeField(null=True)


class Domain(Model):
    id = fields.TextField(pk=True)
    tld: fields.ForeignKeyField[TLD] = fields.ForeignKeyField('models.TLD', 'domains')
    owner = fields.TextField()
    token_id = fields.BigIntField(null=True)


class Record(Model):
    id = fields.TextField(pk=True)
    domain: fields.ForeignKeyField[Domain] = fields.ForeignKeyField('models.Domain', 'records')
    address = fields.TextField(null=True)