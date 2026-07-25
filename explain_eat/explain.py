from typing import Dict, List
from .config import UserProfile


def explain_meal(nutrition_report: Dict[str, object], user_profile: UserProfile) -> List[str]:
    """Generates easy-to-understand explanations for a meal."""
    macros = nutrition_report["macros"]
    explanations = []

    if macros["protein_g"] >= 30:
        explanations.append(
            "This meal contains plenty of protein, which is good for muscle building and satiety."
        )
    else:
        explanations.append(
            "The protein content is still low. A portion of lean meat or legumes would help."
        )

    if macros["sugar_g"] > 15:
        explanations.append(
            "The sugar content is high. This can lead to energy fluctuations."
        )
    else:
        explanations.append(
            "The sugar content is moderate, which helps keep your energy more stable."
        )

    if macros["fiber_g"] < 12:
        explanations.append(
            "Fiber is lacking. More vegetables or whole grains would improve digestion."
        )
    else:
        explanations.append(
            "The amount of fiber is good for digestion and a longer-lasting feeling of fullness."
        )

    explanations.append(
        "The AI analyzes your input and gives you personalized tips for your next meal."
    )

    return explanations


def generate_shopping_recommendations(
    nutrition_report: Dict[str, object],
    detected_items: List[Dict[str, object]],
    user_profile: UserProfile,
) -> List[str]:
    recommendations: List[str] = []
    macros = nutrition_report.get("macros", {})
    total_calories = macros.get("calories", 0)
    protein = macros.get("protein_g", 0)
    fiber = macros.get("fiber_g", 0)

    if protein < 40:
        recommendations.append(
            "Buy about 300 g of chicken or 400 g of tofu to increase your protein intake at the next meal."
        )
    if fiber < 15:
        recommendations.append(
            "Add at least 300 g of vegetables and 200 g of whole-grain products to get more fiber."
        )
    if total_calories < 500:
        recommendations.append(
            "For more energy you can add 100 g of nuts or 150 g of legumes."
        )
    if total_calories > 800:
        recommendations.append(
            "This meal is quite large. For shopping, plan lighter meal components such as salad and vegetables."
        )

    if not recommendations:
        recommendations.append(
            "The AI recommends planning fresh vegetables, lean protein and fiber-rich carbohydrates for your next shopping trip."
        )

    detected_names = [item.get('name', '').lower() for item in detected_items]
    if 'rice' in detected_names and protein < 40:
        recommendations.append(
            "Rice pairs well with chicken or beans; buy about 250 g of chicken and 200 g of beans."
        )

    return recommendations


def recommend_meal_plan(
    nutrition_report: Dict[str, object],
    user_profile: UserProfile,
    detected_items: List[Dict[str, object]],
) -> List[str]:
    """Gives concrete recommendations for what would fit as the next meal."""
    recommendations: List[str] = []
    item_names = [item['name'].lower() for item in detected_items]
    goal = user_profile.goal.lower()

    if 'salad' in item_names or 'vegetable' in item_names or 'broccoli' in item_names:
        recommendations.append('A light quinoa-salad dressing would pair well with this.')
    if 'chicken' in item_names or 'fish' in item_names or 'meat' in item_names:
        recommendations.append('Add steamed vegetables and a small portion of whole-grain rice.')
    if 'bread' in item_names or 'pasta' in item_names:
        recommendations.append('A fresh vegetable side or a light salad adds flavor and fiber.')

    if goal == 'weight_loss':
        recommendations.append('Plan a high-protein meal with vegetables and a moderate portion of carbohydrates.')
    elif goal == 'muscle':
        recommendations.append('Add more lean protein such as legumes, chicken or eggs.')
    else:
        recommendations.append('Aim for balanced portions of protein, carbohydrates and vegetables.')

    # Simple flavor suggestion: combine fresh and savory components.
    recommendations.append('Combine a savory main component with a fresh, slightly tangy side, e.g. a yogurt dip or lemon vegetables.')

    # Fallback
    if not recommendations:
        recommendations.append('Choose a meal with protein, vegetables and a small portion of complex carbohydrates.')

    return recommendations
