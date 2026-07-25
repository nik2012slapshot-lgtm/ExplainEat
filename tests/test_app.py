import pytest
from explain_eat.auth import login_user, register_user
from explain_eat.config import UserProfile
from explain_eat.personalization import create_user_profile
from explain_eat.recognition import recognize_food
from explain_eat.nutrition import analyze_nutrition
from explain_eat.explain import explain_meal


def test_user_profile_creation():
    profile = create_user_profile(25, 68.0, "high", "muscle", ["gluten"])
    assert profile.age == 25
    assert profile.weight == 68.0
    assert profile.activity_level == "high"
    assert "gluten" in profile.allergies


def test_recognize_food_default():
    items = recognize_food(None)
    assert isinstance(items, list)
    assert any(item["name"] == "Whole-grain bread" for item in items)


def test_manual_food_input():
    items = recognize_food(None, manual_items=["Avocado, 1/2 Frucht", "Haehnchenbrust - 120g"])
    assert len(items) == 2
    assert items[0]["name"] == "Avocado"
    assert items[0]["portion"] == "1/2 Frucht"
    assert items[1]["portion"] == "120g"


def test_nutrition_report_contains_macros():
    profile = UserProfile(age=30, weight=70.0, activity_level="moderate", goal="health", allergies=[])
    report = analyze_nutrition([], profile)
    assert "macros" in report
    assert report["macros"]["calories"] == 620


def test_explain_meal_outputs_sentences():
    profile = UserProfile(age=30, weight=70.0, activity_level="moderate", goal="health", allergies=[])
    report = analyze_nutrition([], profile)
    explanations = explain_meal(report, profile)
    assert any("protein" in sentence.lower() for sentence in explanations)


def test_user_registration_and_login():
    username = "test_user_1"
    password = "supersecure"
    registered = register_user(username, password)
    assert registered or login_user(username, password)
    assert login_user(username, password)
