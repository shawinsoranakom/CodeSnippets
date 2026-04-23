def _convert_citation_to_v1(citation: dict[str, Any]) -> types.Annotation:
    standard_citation: types.Citation = {"type": "citation"}
    if "title" in citation:
        standard_citation["title"] = citation["title"]
    if (
        (source_content := citation.get("source_content"))
        and isinstance(source_content, list)
        and all(isinstance(item, dict) for item in source_content)
    ):
        standard_citation["cited_text"] = "".join(
            item.get("text", "") for item in source_content
        )

    known_fields = {"type", "source_content", "title", "index", "extras"}

    for key, value in citation.items():
        if key not in known_fields:
            if "extras" not in standard_citation:
                standard_citation["extras"] = {}
            standard_citation["extras"][key] = value

    return standard_citation