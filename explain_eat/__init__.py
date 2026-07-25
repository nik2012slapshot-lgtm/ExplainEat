"""ExplainEat core package."""

from .auth import login_user, register_user
from .ai_vision import get_food_ai
from .config import UserProfile
from .recognition import recognize_food
from .nutrition import analyze_nutrition
from .explain import explain_meal
from .personalization import create_user_profile

__all__ = [
    "login_user",
    "register_user",
    "get_food_ai",
    "UserProfile",
    "recognize_food",
    "analyze_nutrition",
    "explain_meal",
    "create_user_profile",
]
