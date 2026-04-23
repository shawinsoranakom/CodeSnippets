def _get_anime_recommendations(anime_id: int) -> List[Dict[str, Any]]:
    try:
        recs_url = f"https://api.jikan.moe/v4/anime/{anime_id}/recommendations"
        recs_response = requests.get(recs_url)
        if recs_response.status_code == 429:
            time.sleep(0.5)
            recs_response = requests.get(recs_url)
        if recs_response.status_code != 200:
            return []
        recs_data = recs_response.json()
        if "data" not in recs_data:
            return []

        recommendations = []
        for rec in recs_data["data"][:5]:
            if "entry" in rec:
                title = rec["entry"].get("title", "")
                if title:
                    recommendations.append(title)
        return recommendations
    except Exception as _:
        return []