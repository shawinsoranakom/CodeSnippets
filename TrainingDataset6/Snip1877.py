def _construct_html_link(
    link_text: str,
    attributes: list[HTMLLinkAttribute],
    lang_code: str,
) -> str:
    """
    Reconstruct HTML link, adjusting the URL for the given language code if needed.
    """

    attributes_upd: list[HTMLLinkAttribute] = []
    for attribute in attributes:
        if attribute["name"] == "href":
            original_url = attribute["value"]
            url = _add_lang_code_to_url(original_url, lang_code)
            attributes_upd.append(
                HTMLLinkAttribute(name="href", quote=attribute["quote"], value=url)
            )
        else:
            attributes_upd.append(attribute)

    attrs_str = " ".join(
        f"{attribute['name']}={attribute['quote']}{attribute['value']}{attribute['quote']}"
        for attribute in attributes_upd
    )
    return f"<a {attrs_str}>{link_text}</a>"