from pydantic import BaseModel
from enum import Enum
from datetime import datetime

class Gender(Enum):
    m = 'M'
    w = 'W'
    everyone = 'ALL '

class Income_Group(Enum):
    low = 'A'
    ab_low = 'AB'
    avg = 'B'
    ab_avg = 'BC'
    high = 'C'

class TA(BaseModel):
    gender: Gender
    min_age: float
    max_age: float = float('inf')
    income_group: Income_Group | None = None

class Dates_Interval(BaseModel):
    start: datetime
    finish: datetime
    ...