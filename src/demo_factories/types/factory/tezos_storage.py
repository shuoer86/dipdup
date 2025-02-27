# generated by datamodel-codegen:
#   filename:  tezos_storage.json

from __future__ import annotations

from typing import Dict
from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import Extra


class Ledger(BaseModel):
    class Config:
        extra = Extra.forbid

    allowances: List[str]
    balance: str
    frozen_balance: str


class TokenList(BaseModel):
    class Config:
        extra = Extra.forbid

    address: str
    nat: str


class Key(BaseModel):
    class Config:
        extra = Extra.forbid

    address: str
    nat: str


class TokenToExchangeItem(BaseModel):
    class Config:
        extra = Extra.forbid

    key: Key
    value: str


class UserRewards(BaseModel):
    class Config:
        extra = Extra.forbid

    reward: str
    reward_paid: str


class Voters(BaseModel):
    class Config:
        extra = Extra.forbid

    candidate: Optional[str]
    last_veto: str
    veto: str
    vote: str


class FactoryStorage(BaseModel):
    class Config:
        extra = Extra.forbid

    baker_validator: str
    counter: str
    dex_lambdas: Dict[str, str]
    ledger: Dict[str, Ledger]
    metadata: Dict[str, str]
    token_lambdas: Dict[str, str]
    token_list: Dict[str, TokenList]
    token_to_exchange: List[TokenToExchangeItem]
    user_rewards: Dict[str, UserRewards]
    vetos: Dict[str, str]
    voters: Dict[str, Voters]
    votes: Dict[str, str]
