def analyze_posts_sentiment(posts_data):
    session_id = str(uuid.uuid4())
    analysis_agent = Agent(
        model=OpenAIChat(id="gpt-4o"),
        instructions=SENTIMENT_AGENT_INSTRUCTIONS,
        description=SENTIMENT_AGENT_DESCRIPTION,
        use_json_mode=True,
        response_model=AnalysisResponse,
        session_id=session_id,
    )
    posts_prompt = "Analyze the sentiment and categorize the following social media posts:\n\n"
    valid_posts = []
    for post in posts_data:
        post_text = post.get("post_text", "")
        post_id = post.get("post_id", "")
        if post_text and post_id:
            valid_posts.append(post)
            posts_prompt += f"POST (ID: {post_id}):\n{post_text}\n\n"
    if not valid_posts:
        return []
    response = analysis_agent.run(posts_prompt, session_id=session_id)
    analysis_results = response.to_dict()["content"]["analyzed_posts"]
    validated_results = []
    valid_post_ids = {post.get("post_id") for post in valid_posts}
    for analysis in analysis_results:
        if analysis.get("post_id") in valid_post_ids:
            validated_results.append(analysis)
        else:
            print(f"Warning: Analysis returned with invalid post_id: {analysis.get('post_id')}")
    return validated_results