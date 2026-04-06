def get_users_to_write(
    *,
    counter: Counter[str],
    authors: dict[str, Author],
    min_count: int = 2,
) -> dict[str, Any]:
    users: dict[str, Any] = {}
    for user, count in counter.most_common():
        if count >= min_count:
            author = authors[user]
            users[user] = {
                "login": user,
                "count": count,
                "avatarUrl": author.avatarUrl,
                "url": author.url,
            }
    return users