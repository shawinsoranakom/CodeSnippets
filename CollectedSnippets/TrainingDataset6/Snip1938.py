def get_top_users(
    *,
    counter: Counter[str],
    authors: dict[str, Author],
    skip_users: Container[str],
    min_count: int = 2,
) -> list[dict[str, Any]]:
    users: list[dict[str, Any]] = []
    for commenter, count in counter.most_common(50):
        if commenter in skip_users:
            continue
        if count >= min_count:
            author = authors[commenter]
            users.append(
                {
                    "login": commenter,
                    "count": count,
                    "avatarUrl": author.avatarUrl,
                    "url": author.url,
                }
            )
    return users