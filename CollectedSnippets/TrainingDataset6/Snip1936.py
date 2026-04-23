def get_discussion_nodes(settings: Settings) -> list[DiscussionsNode]:
    discussion_nodes: list[DiscussionsNode] = []
    discussion_edges = get_graphql_question_discussion_edges(settings=settings)

    while discussion_edges:
        for discussion_edge in discussion_edges:
            discussion_nodes.append(discussion_edge.node)
        last_edge = discussion_edges[-1]
        discussion_edges = get_graphql_question_discussion_edges(
            settings=settings, after=last_edge.cursor
        )
    return discussion_nodes