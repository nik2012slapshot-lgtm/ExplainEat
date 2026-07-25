from .config import UserProfile
from typing import List


def create_user_profile(
    age: int,
    weight: float,
    activity_level: str,
    goal: str,
    allergies: List[str],
) -> UserProfile:
    """Creates a user profile for personalized nutrition recommendations."""
    normalized_activity = activity_level.lower()
    if normalized_activity not in {"low", "moderate", "high"}:
        normalized_activity = "moderate"

    normalized_goal = goal.lower()
    if normalized_goal not in {"health", "muscle", "weight_loss"}:
        normalized_goal = "health"

    return UserProfile(
        age=age,
        weight=weight,
        activity_level=normalized_activity,
        goal=normalized_goal,
        allergies=[item.strip().lower() for item in allergies if item],
    )
