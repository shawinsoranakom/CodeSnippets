def get_graphql_question_discussion_edges(
    *,
    settings: Settings,
    after: str | None = None,
) -> list[DiscussionsEdge]:
    with rate_limiter:
        data = get_graphql_response(
            settings=settings,
            query=discussions_query,
            after=after,
            category_id=questions_category_id,
        )

    rate_limiter.update_request_info(
        cost=data["data"]["rateLimit"]["cost"],
        remaining=data["data"]["rateLimit"]["remaining"],
        reset_at=data["data"]["rateLimit"]["resetAt"],
    )
    graphql_response = DiscussionsResponse.model_validate(data)
    return graphql_response.data.repository.discussions.edges