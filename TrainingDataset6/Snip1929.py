def get_graphql_translation_discussion_comments_edges(
    *, settings: Settings, discussion_number: int, after: str | None = None
) -> list[CommentsEdge]:
    data = get_graphql_response(
        settings=settings,
        query=translation_discussion_query,
        discussion_number=discussion_number,
        after=after,
    )
    graphql_response = CommentsResponse.model_validate(data)
    return graphql_response.data.repository.discussion.comments.edges