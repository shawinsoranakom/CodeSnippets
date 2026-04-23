def create_meal_plan(dietary_preference: str = "balanced", people: int = 2, days: int = 7, budget: str = "moderate") -> Dict:
    """Create comprehensive weekly meal plan with nutrition and shopping list."""

    meals = {
        "breakfast": [
            {"name": "Overnight Oats with Berries", "calories": 320, "protein": 12, "cost": 2.50},
            {"name": "Veggie Scramble with Toast", "calories": 280, "protein": 18, "cost": 3.20},
            {"name": "Greek Yogurt Parfait", "calories": 250, "protein": 15, "cost": 2.80}
        ],
        "lunch": [
            {"name": "Quinoa Buddha Bowl", "calories": 420, "protein": 16, "cost": 4.50},
            {"name": "Chicken Caesar Wrap", "calories": 380, "protein": 25, "cost": 5.20},
            {"name": "Lentil Vegetable Soup", "calories": 340, "protein": 18, "cost": 3.80}
        ],
        "dinner": [
            {"name": "Grilled Salmon with Vegetables", "calories": 520, "protein": 35, "cost": 8.90},
            {"name": "Chicken Stir Fry with Brown Rice", "calories": 480, "protein": 32, "cost": 6.50},
            {"name": "Vegetable Curry with Quinoa", "calories": 450, "protein": 15, "cost": 5.20}
        ]
    }

    budget_multipliers = {"low": 0.7, "moderate": 1.0, "high": 1.3}
    multiplier = budget_multipliers.get(budget.lower(), 1.0)

    weekly_plan = {}
    shopping_list = set()
    total_weekly_cost = 0
    total_weekly_calories = 0
    total_weekly_protein = 0

    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for day in day_names[:days]:
        daily_meals = {}
        daily_calories = 0
        daily_protein = 0
        daily_cost = 0

        for meal_type in ["breakfast", "lunch", "dinner"]:
            selected_meal = random.choice(meals[meal_type])
            daily_meals[meal_type] = {
                "name": selected_meal["name"],
                "calories": selected_meal["calories"],
                "protein": selected_meal["protein"]
            }

            meal_cost = selected_meal["cost"] * people * multiplier
            daily_calories += selected_meal["calories"]
            daily_protein += selected_meal["protein"]
            daily_cost += meal_cost

            # Add to shopping list
            if "chicken" in selected_meal["name"].lower():
                shopping_list.add("Chicken breast")
            if "salmon" in selected_meal["name"].lower():
                shopping_list.add("Salmon fillets")
            if "vegetable" in selected_meal["name"].lower():
                shopping_list.update(["Mixed vegetables", "Onions", "Garlic"])
            if "quinoa" in selected_meal["name"].lower():
                shopping_list.add("Quinoa")
            if "oats" in selected_meal["name"].lower():
                shopping_list.add("Rolled oats")

        weekly_plan[day] = daily_meals
        total_weekly_cost += daily_cost
        total_weekly_calories += daily_calories
        total_weekly_protein += daily_protein

    # Generate insights
    avg_daily_calories = round(total_weekly_calories / days)
    avg_daily_protein = round(total_weekly_protein / days, 1)

    insights = []
    if avg_daily_calories < 1800:
        insights.append("⚠️ Consider adding healthy snacks to meet calorie needs")
    elif avg_daily_calories > 2200:
        insights.append("💡 Calorie-dense meals - great for active lifestyles")

    if avg_daily_protein > 80:
        insights.append("✅ Excellent protein intake for muscle maintenance")
    elif avg_daily_protein < 60:
        insights.append("💡 Consider adding more protein sources")

    return {
        "meal_plan": weekly_plan,
        "total_weekly_cost": round(total_weekly_cost, 2),
        "cost_per_person_per_day": round(total_weekly_cost / (people * days), 2),
        "avg_daily_calories": avg_daily_calories,
        "avg_daily_protein": avg_daily_protein,
        "dietary_preference": dietary_preference,
        "serves": people,
        "days": days,
        "shopping_list": sorted(list(shopping_list)),
        "insights": insights
    }