def search_scraper(anime_name: str) -> list:
    """[summary]

    Take an url and
    return list of anime after scraping the site.

    >>> type(search_scraper("demon_slayer"))
    <class 'list'>

    Args:
        anime_name (str): [Name of anime]

    Raises:
        e: [Raises exception on failure]

    Returns:
        [list]: [List of animes]
    """

    # concat the name to form the search url.
    search_url = f"{BASE_URL}/search?keyword={anime_name}"

    response = httpx.get(
        search_url, headers={"UserAgent": UserAgent().chrome}, timeout=10
    )  # request the url.

    # Is the response ok?
    response.raise_for_status()

    # parse with soup.
    soup = BeautifulSoup(response.text, "html.parser")

    # get list of anime
    anime_ul = soup.find("ul", {"class": "items"})
    if anime_ul is None or isinstance(anime_ul, NavigableString):
        msg = f"Could not find and anime with name {anime_name}"
        raise ValueError(msg)
    anime_li = anime_ul.children

    # for each anime, insert to list. the name and url.
    anime_list = []
    for anime in anime_li:
        if isinstance(anime, Tag):
            anime_url = anime.find("a")
            if anime_url is None or isinstance(anime_url, NavigableString):
                continue
            anime_title = anime.find("a")
            if anime_title is None or isinstance(anime_title, NavigableString):
                continue

            anime_list.append({"title": anime_title["title"], "url": anime_url["href"]})

    return anime_list