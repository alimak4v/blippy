from pydantic import BaseModel
from typing import List

class Tx(BaseModel):
    sender: str
    to: str
    amount: float

class State(BaseModel):
    name: str
    address: str
    balance: float
    history: List[Tx] = []
