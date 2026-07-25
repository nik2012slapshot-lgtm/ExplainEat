from dataclasses import dataclass
from typing import List


@dataclass
class UserProfile:
    age: int
    weight: float
    activity_level: str
    goal: str
    allergies: List[str]


def default_user_profile() -> UserProfile:
    return UserProfile(age=30, weight=70.0, activity_level="moderate", goal="health", allergies=[])
