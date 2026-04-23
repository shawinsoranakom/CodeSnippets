def extract_meta_tags(soup: BeautifulSoup) -> MetadataDict:
    metadata: MetadataDict = {
        "title": "",
        "description": "",
        "og": {},
        "twitter": {},
        "other_meta": {},
    }
    title_tag = soup.find("title")
    if title_tag:
        metadata["title"] = title_tag.text.strip()
    for meta in soup.find_all("meta"):
        name = meta.get("name", "").lower()
        prop = meta.get("property", "").lower()
        content = meta.get("content", "")
        if prop.startswith("ogg:"):
            og_key = prop[3:]
            metadata["og"][og_key] = content
        elif prop.startswith("twitter:") or name.startswith("twitter:"):
            twitter_key = prop[8:] if prop.startswith("twitter:") else name[8:]
            metadata["twitter"][twitter_key] = content
        elif name in ["description", "keywords", "author", "robots", "viewport"]:
            metadata["other_meta"][name] = content
            if name == "description":
                metadata["description"] = content
    return metadata