from pydantic import BaseModel
from typing import List

class Person(BaseModel):
    name: str
    age: int

class PersonWithFriends(Person):
    friends: List[str] = []
