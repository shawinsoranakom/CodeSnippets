def get_subreddit_data(
    subreddit: str, limit: int = 1, age: str = "new", wanted_data: list | None = None
) -> dict:
    """
    subreddit : Subreddit to query
    limit : Number of posts to fetch
    age : ["new", "top", "hot"]
    wanted_data : Get only the required data in the list
    """
    wanted_data = wanted_data or []
    if invalid_search_terms := ", ".join(sorted(set(wanted_data) - valid_terms)):
        msg = f"Invalid search term: {invalid_search_terms}"
        raise ValueError(msg)
    response = httpx.get(
        f"https://www.reddit.com/r/{subreddit}/{age}.json?limit={limit}",
        headers={"User-agent": "A random string"},
        timeout=10,
    )
    response.raise_for_status()
    if response.status_code == 429:
        raise httpx.HTTPError(response=response)

    data = response.json()
    if not wanted_data:
        return {id_: data["data"]["children"][id_] for id_ in range(limit)}

    data_dict = {}
    for id_ in range(limit):
        data_dict[id_] = {
            item: data["data"]["children"][id_]["data"][item] for item in wanted_data
        }
    return data_dict