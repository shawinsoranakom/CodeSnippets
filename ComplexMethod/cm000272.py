def search_anime_episode_list(episode_endpoint: str) -> list:
    """[summary]

    Take an url and
    return list of episodes after scraping the site
    for an url.

    >>> type(search_anime_episode_list("/anime/kimetsu-no-yaiba"))
    <class 'list'>

    Args:
        episode_endpoint (str): [Endpoint of episode]

    Raises:
        e: [description]

    Returns:
        [list]: [List of episodes]
    """

    request_url = f"{BASE_URL}{episode_endpoint}"

    response = httpx.get(
        url=request_url, headers={"UserAgent": UserAgent().chrome}, timeout=10
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # With this id. get the episode list.
    episode_page_ul = soup.find("ul", {"id": "episode_related"})
    if episode_page_ul is None or isinstance(episode_page_ul, NavigableString):
        msg = f"Could not find any anime eposiodes with name {anime_name}"
        raise ValueError(msg)
    episode_page_li = episode_page_ul.children

    episode_list = []
    for episode in episode_page_li:
        if isinstance(episode, Tag):
            url = episode.find("a")
            if url is None or isinstance(url, NavigableString):
                continue
            title = episode.find("div", {"class": "name"})
            if title is None or isinstance(title, NavigableString):
                continue

            episode_list.append(
                {"title": title.text.replace(" ", ""), "url": url["href"]}
            )

    return episode_list