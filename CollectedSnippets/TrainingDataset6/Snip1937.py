def get_discussions_experts(
    discussion_nodes: list[DiscussionsNode],
) -> DiscussionExpertsResults:
    commenters = Counter[str]()
    last_month_commenters = Counter[str]()
    three_months_commenters = Counter[str]()
    six_months_commenters = Counter[str]()
    one_year_commenters = Counter[str]()
    authors: dict[str, Author] = {}

    now = datetime.now(tz=timezone.utc)
    one_month_ago = now - timedelta(days=30)
    three_months_ago = now - timedelta(days=90)
    six_months_ago = now - timedelta(days=180)
    one_year_ago = now - timedelta(days=365)

    for discussion in discussion_nodes:
        discussion_author_name = None
        if discussion.author:
            authors[discussion.author.login] = discussion.author
            discussion_author_name = discussion.author.login
        discussion_commentors: dict[str, datetime] = {}
        for comment in discussion.comments.nodes:
            if (
                comment.minimizedReason not in MINIMIZED_COMMENTS_REASONS_TO_EXCLUDE
                and comment.author
            ):
                authors[comment.author.login] = comment.author
                if comment.author.login != discussion_author_name:
                    author_time = discussion_commentors.get(
                        comment.author.login, comment.createdAt
                    )
                    discussion_commentors[comment.author.login] = max(
                        author_time, comment.createdAt
                    )
            for reply in comment.replies.nodes:
                if (
                    reply.minimizedReason not in MINIMIZED_COMMENTS_REASONS_TO_EXCLUDE
                    and reply.author
                ):
                    authors[reply.author.login] = reply.author
                    if reply.author.login != discussion_author_name:
                        author_time = discussion_commentors.get(
                            reply.author.login, reply.createdAt
                        )
                        discussion_commentors[reply.author.login] = max(
                            author_time, reply.createdAt
                        )
        for author_name, author_time in discussion_commentors.items():
            commenters[author_name] += 1
            if author_time > one_month_ago:
                last_month_commenters[author_name] += 1
            if author_time > three_months_ago:
                three_months_commenters[author_name] += 1
            if author_time > six_months_ago:
                six_months_commenters[author_name] += 1
            if author_time > one_year_ago:
                one_year_commenters[author_name] += 1
    discussion_experts_results = DiscussionExpertsResults(
        authors=authors,
        commenters=commenters,
        last_month_commenters=last_month_commenters,
        three_months_commenters=three_months_commenters,
        six_months_commenters=six_months_commenters,
        one_year_commenters=one_year_commenters,
    )
    return discussion_experts_results