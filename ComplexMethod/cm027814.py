def estimate_costs(ingredients: List[str], servings: int = 4) -> Dict:
    """Detailed cost estimation with budget tips."""
    prices = {
        "chicken breast": 6.99, "ground beef": 5.99, "salmon": 12.99,
        "rice": 2.99, "pasta": 1.99, "broccoli": 2.99, "tomatoes": 3.99,
        "cheese": 5.99, "onion": 1.49, "garlic": 2.99, "olive oil": 7.99
    }

    cost_breakdown = []
    total_cost = 0

    for ingredient in ingredients:
        ingredient_lower = ingredient.lower().strip()
        cost = 3.99  # default

        for key, price in prices.items():
            if key in ingredient_lower or any(word in ingredient_lower for word in key.split()):
                cost = price
                break

        adjusted_cost = (cost * servings) / 4
        total_cost += adjusted_cost
        cost_breakdown.append({
            "name": ingredient.title(),
            "cost": round(adjusted_cost, 2)
        })

    # Budget tips
    budget_tips = []
    if total_cost > 30:
        budget_tips.append("💡 Consider buying in bulk for better prices")
    if total_cost > 40:
        budget_tips.append("💡 Look for seasonal alternatives to reduce costs")
    budget_tips.append("💡 Shop at local markets for fresher, cheaper produce")

    return {
        "total_cost": round(total_cost, 2),
        "cost_per_serving": round(total_cost / servings, 2),
        "servings": servings,
        "breakdown": cost_breakdown,
        "budget_tips": budget_tips
    }