def _format_anime_info(anime: Dict[str, Any]) -> Dict[str, Any]:
    try:
        mal_id = anime.get("mal_id")
        title = anime.get("title", "Unknown Anime")
        title_english = anime.get("title_english")
        if title_english and title_english != title:
            title_display = f"{title} ({title_english})"
        else:
            title_display = title

        url = anime.get("url", f"https://myanimelist.net/anime/{mal_id}")
        synopsis = anime.get("synopsis", "No synopsis available.")
        synopsis = html.unescape(synopsis)
        episodes = anime.get("episodes", "Unknown")
        status = anime.get("status", "Unknown")
        aired_string = anime.get("aired", {}).get("string", "Unknown")
        score = anime.get("score", "N/A")
        scored_by = anime.get("scored_by", 0)
        rank = anime.get("rank", "N/A")
        popularity = anime.get("popularity", "N/A")
        studios = []
        for studio in anime.get("studios", []):
            if "name" in studio:
                studios.append(studio["name"])
        studio_text = ", ".join(studios) if studios else "Unknown"
        genres = []
        for genre in anime.get("genres", []):
            if "name" in genre:
                genres.append(genre["name"])
        genre_text = ", ".join(genres) if genres else "Unknown"
        themes = []
        for theme in anime.get("themes", []):
            if "name" in theme:
                themes.append(theme["name"])
        demographics = []
        for demo in anime.get("demographics", []):
            if "name" in demo:
                demographics.append(demo["name"])
        content = f"Title: {title_display}\n"
        content += f"Score: {score} (rated by {scored_by:,} users)\n"
        content += f"Rank: {rank}, Popularity: {popularity}\n"
        content += f"Episodes: {episodes}\n"
        content += f"Status: {status}\n"
        content += f"Aired: {aired_string}\n"
        content += f"Studio: {studio_text}\n"
        content += f"Genres: {genre_text}\n"
        if themes:
            content += f"Themes: {', '.join(themes)}\n"
        if demographics:
            content += f"Demographics: {', '.join(demographics)}\n"
        content += f"\nSynopsis:\n{synopsis}\n"
        if mal_id:
            recommendations = _get_anime_recommendations(mal_id)
            if recommendations:
                content += f"\nSimilar Anime: {', '.join(recommendations)}\n"
        summary = f"{title_display} - {genre_text} anime with {episodes} episodes. "
        summary += f"Rating: {score}/10. "
        if synopsis:
            short_synopsis = synopsis[:150] + "..." if len(synopsis) > 150 else synopsis
            summary += short_synopsis
        categories = ["anime", "japanese animation", "entertainment"]
        if genres:
            categories.extend(genres[:5])
        if themes:
            categories.extend(themes[:2])
        return {
            "id": f"jikan_{mal_id}",
            "title": f"{title_display} (Anime)",
            "url": url,
            "published_date": aired_string.split(" to ")[0] if " to " in aired_string else aired_string,
            "description": content,
            "source_id": "jikan",
            "source_name": "MyAnimeList",
            "categories": categories,
            "is_scrapping_required": False,

        }
    except Exception as _:
        return {
            "id": f"jikan_{anime.get('mal_id', 'unknown')}",
            "title": f"{anime.get('title', 'Unknown Anime')} (Anime)",
            "url": anime.get("url", "https://myanimelist.net"),
            "published_date": None,
            "description": anime.get("synopsis", "No information available."),
            "source_id": "jikan",
            "source_name": "MyAnimeList",
            "categories": ["anime", "japanese animation", "entertainment"],
            "is_scrapping_required": False,
        }