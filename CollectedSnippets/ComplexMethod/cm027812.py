def search_recipes(ingredients: str, diet_type: Optional[str] = None) -> Dict:
    """Search for detailed recipes with cooking instructions."""
    if not SPOONACULAR_API_KEY:
        return {"error": "Spoonacular API key not found"}

    url = "https://api.spoonacular.com/recipes/findByIngredients"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "ingredients": ingredients,
        "number": 5,
        "ranking": 2,
        "ignorePantry": True
    }
    if diet_type:
        params["diet"] = diet_type

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        recipes = response.json()

        detailed_recipes = []
        for recipe in recipes[:3]:
            detail_url = f"https://api.spoonacular.com/recipes/{recipe['id']}/information"
            detail_response = requests.get(detail_url, params={"apiKey": SPOONACULAR_API_KEY}, timeout=10)

            if detail_response.status_code == 200:
                detail_data = detail_response.json()
                detailed_recipes.append({
                    "id": recipe['id'],
                    "title": recipe['title'],
                    "ready_in_minutes": detail_data.get('readyInMinutes', 'N/A'),
                    "servings": detail_data.get('servings', 'N/A'),
                    "health_score": detail_data.get('healthScore', 0),
                    "used_ingredients": [i['name'] for i in recipe['usedIngredients']],
                    "missing_ingredients": [i['name'] for i in recipe['missedIngredients']],
                    "instructions": detail_data.get('instructions', 'Instructions not available')
                })

        return {
            "recipes": detailed_recipes,
            "total_found": len(recipes)
        }
    except:
        return {"error": "Recipe search failed"}