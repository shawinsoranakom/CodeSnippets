def analyze_nutrition(recipe_name: str) -> Dict:
    """Get nutrition analysis for a recipe by searching for it."""
    if not SPOONACULAR_API_KEY:
        return {"error": "API key not found"}

    # First search for the recipe
    search_url = "https://api.spoonacular.com/recipes/complexSearch"
    search_params = {
        "apiKey": SPOONACULAR_API_KEY,
        "query": recipe_name,
        "number": 1,
        "addRecipeInformation": True,
        "addRecipeNutrition": True
    }

    try:
        search_response = requests.get(search_url, params=search_params, timeout=15)
        search_response.raise_for_status()
        search_data = search_response.json()

        if not search_data.get('results'):
            return {"error": f"No recipe found for '{recipe_name}'"}

        recipe = search_data['results'][0]

        if 'nutrition' not in recipe:
            return {"error": "No nutrition data available for this recipe"}

        nutrients = {n['name']: n['amount'] for n in recipe['nutrition']['nutrients']}
        calories = round(nutrients.get('Calories', 0))
        protein = round(nutrients.get('Protein', 0), 1)
        carbs = round(nutrients.get('Carbohydrates', 0), 1)
        fat = round(nutrients.get('Fat', 0), 1)
        fiber = round(nutrients.get('Fiber', 0), 1)
        sodium = round(nutrients.get('Sodium', 0), 1)

        # Health insights
        health_insights = []
        if protein > 25:
            health_insights.append("✅ High protein - great for muscle building")
        if fiber > 5:
            health_insights.append("✅ High fiber - supports digestive health")
        if sodium < 600:
            health_insights.append("✅ Low sodium - heart-friendly")
        if calories < 400:
            health_insights.append("✅ Low calorie - good for weight management")

        return {
            "recipe_title": recipe.get('title', 'Recipe'),
            "servings": recipe.get('servings', 1),
            "ready_in_minutes": recipe.get('readyInMinutes', 'N/A'),
            "health_score": recipe.get('healthScore', 0),
            "calories": calories,
            "protein": protein,
            "carbs": carbs,
            "fat": fat,
            "fiber": fiber,
            "sodium": sodium,
            "health_insights": health_insights
        }
    except:
        return {"error": "Nutrition analysis failed"}