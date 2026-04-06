def get_graphql_translation_discussions(
    *, settings: Settings
) -> list[AllDiscussionsDiscussionNode]:
    data = get_graphql_response(
        settings=settings,
        query=all_discussions_query,
        category_id=questions_translations_category_id,
    )
    graphql_response = AllDiscussionsResponse.model_validate(data)
    return graphql_response.data.repository.discussions.nodes