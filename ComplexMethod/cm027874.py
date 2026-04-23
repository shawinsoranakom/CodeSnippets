def check_ad(soup):
    is_ad = False
    ad_label = soup.find(
        lambda tag: tag.name and tag.text and tag.text.strip() == "Ad" and "r-bcqeeo" in tag.get("class", []) if hasattr(tag, "get") else False
    )
    if ad_label:
        is_ad = True
    username_element = soup.select_one("div[data-testid='User-Name'] a[role='link'] span")
    if username_element and username_element.text.strip() in [
        "Premium",
        "Twitter",
        "X",
    ]:
        is_ad = True
    handle_element = soup.select_one("div[data-testid='User-Name'] div[dir='ltr'] span")
    if handle_element and "@premium" in handle_element.text:
        is_ad = True
    ad_tracking_links = soup.select("a[href*='referring_page=ad_'], a[href*='twclid=']")
    if ad_tracking_links:
        is_ad = True
    return is_ad