def get_users_to_write(
    *,
    counter: Counter[str],
    authors: dict[str, Author],
    min_count: int = 2,
) -> list[dict[str, Any]]:
    users: dict[str, Any] = {}
    users_list: list[dict[str, Any]] = []
    for user, count in counter.most_common(60):
        if count >= min_count:
            author = authors[user]
            user_data = {
                "login": user,
                "count": count,
                "avatarUrl": author.avatarUrl,
                "url": author.url,
            }
            users[user] = user_data
            users_list.append(user_data)
    return users_list