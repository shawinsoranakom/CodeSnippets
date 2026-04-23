def process_articles_for_embedding(tracking_db_path=None, openai_api_key=None, batch_size=20, delay_range=(1, 3)):
    if tracking_db_path is None:
        tracking_db_path = get_tracking_db_path()
    if openai_api_key is None:
        raise ValueError("OpenAI API key is required")
    create_embedding_table(tracking_db_path)
    client = OpenAI(api_key=openai_api_key)
    articles = get_articles_without_embeddings(tracking_db_path, limit=batch_size)
    if not articles:
        print("No articles found that need embeddings")
        return {"total_articles": 0, "success_count": 0, "failed_count": 0}
    article_ids = [article["id"] for article in articles]
    mark_articles_as_processing(tracking_db_path, article_ids)
    stats = {"total_articles": len(articles), "success_count": 0, "failed_count": 0}
    for i, article in enumerate(articles):
        article_id = article["id"]
        try:
            print(f"[{i + 1}/{len(articles)}] Generating embedding for article {article_id}: {article['title']}")
            text = prepare_article_text(article)
            embedding, model = generate_embedding(client, text)
            if embedding:
                success = store_embedding(tracking_db_path, article_id, embedding, model)
                if success:
                    print(f"Successfully stored embedding for article {article_id}")
                    stats["success_count"] += 1
                else:
                    print(f"Failed to store embedding for article {article_id}")
                    stats["failed_count"] += 1
            else:
                print(f"Failed to generate embedding for article {article_id}")
                stats["failed_count"] += 1
        except Exception as e:
            print(f"Error processing article {article_id}: {str(e)}")
            stats["failed_count"] += 1
        if i < len(articles) - 1:
            delay = random.uniform(delay_range[0], delay_range[1])
            time.sleep(delay)
    return stats