def read_links(html: str, base: str) -> set[str]:
    soup = BeautifulSoup(html, "html.parser")
    for selector in [
            "main",
            ".main-content-wrapper",
            ".main-content",
            ".emt-container-inner",
            ".content-wrapper",
            "#content",
            "#mainContent",
        ]:
        select = soup.select_one(selector)
        if select:
            soup = select
            break
    urls = []
    for link in soup.select("a"):
        if "rel" not in link.attrs or "nofollow" not in link.attrs["rel"]:
            url = link.attrs.get("href")
            if url and url.startswith("https://") or url.startswith("/"):
                urls.append(url.split("#")[0])
    return set([urllib.parse.urljoin(base, link) for link in urls])