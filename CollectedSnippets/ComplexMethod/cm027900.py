def process_article_with_ai(client, article, max_tokens=8000):
    clean_text = extract_clean_text(article["raw_content"], max_tokens)
    metadata = article.get("metadata", {})
    title = article["title"]
    url = article["url"]
    description = ""
    if metadata and isinstance(metadata, dict):
        if "description" in metadata:
            description = metadata["description"]
        elif "og" in metadata and "description" in metadata["og"]:
            description = metadata["og"]["description"]
    try:
        response = client.chat.completions.create(
            model=WEB_PAGE_ANALYSE_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": MODEL_INSTRUCTION,
                },
                {
                    "role": "user",
                    "content": f"""
                                Analyze this article and provide a structured output with three components:

                                1. A list of 3-5 relevant categories for this article
                                2. A concise 2-3 sentence summary of the article
                                3. The extracted main article content, removing any navigation, ads, or irrelevant elements

                                Article Title: {title}
                                Article URL: {url}
                                Description: {description}

                                Article Text:
                                {clean_text}

                                Provide your response as a JSON object with these keys:
                                - categories: an array of 3-5 relevant categories (as strings)
                                - summary: a 2-3 sentence summary of the article
                                - content: the cleaned main article content
                                """,
                },
            ],
            temperature=0.3,
            max_tokens=1500,
        )
        response_json = json.loads(response.choices[0].message.content)
        categories = response_json.get("categories", [])
        if isinstance(categories, str):
            categories = [cat.strip() for cat in categories.split(",") if cat.strip()]
        results = {
            "categories": categories,
            "summary": response_json.get("summary", ""),
            "content": response_json.get("content", ""),
        }
        return results, True, None
    except Exception as e:
        error_message = str(e)
        print(f"Error processing article with AI: {error_message}")
        return None, False, error_message