def _extract_text_from_paragraph(paragraph: dict[str, Any]) -> str:
    """Extracts the text content from a paragraph element"""
    text_elements = []
    for element in paragraph.get("elements", []):
        if "textRun" in element:
            text_elements.append(element["textRun"].get("content", ""))

        # Handle links
        if "textStyle" in element and "link" in element["textStyle"]:
            text_elements.append(f"({element['textStyle']['link'].get('url', '')})")

        if "person" in element:
            name = element["person"].get("personProperties", {}).get("name", "")
            email = element["person"].get("personProperties", {}).get("email", "")
            person_str = "<Person|"
            if name:
                person_str += f"name: {name}, "
            if email:
                person_str += f"email: {email}"
            person_str += ">"
            text_elements.append(person_str)

        if "richLink" in element:
            props = element["richLink"].get("richLinkProperties", {})
            title = props.get("title", "")
            uri = props.get("uri", "")
            link_str = f"[{title}]({uri})"
            text_elements.append(link_str)

    return "".join(text_elements)