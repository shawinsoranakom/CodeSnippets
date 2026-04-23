def _convert_citation_to_v1(citation: dict[str, Any]) -> types.Annotation:
    citation_type = citation.get("type")

    if citation_type == "web_search_result_location":
        url_citation: types.Citation = {
            "type": "citation",
            "cited_text": citation["cited_text"],
            "url": citation["url"],
        }
        if title := citation.get("title"):
            url_citation["title"] = title
        known_fields = {"type", "cited_text", "url", "title", "index", "extras"}
        for key, value in citation.items():
            if key not in known_fields:
                if "extras" not in url_citation:
                    url_citation["extras"] = {}
                url_citation["extras"][key] = value

        return url_citation

    if citation_type in {
        "char_location",
        "content_block_location",
        "page_location",
        "search_result_location",
    }:
        document_citation: types.Citation = {
            "type": "citation",
            "cited_text": citation["cited_text"],
        }
        if "document_title" in citation:
            document_citation["title"] = citation["document_title"]
        elif title := citation.get("title"):
            document_citation["title"] = title
        known_fields = {
            "type",
            "cited_text",
            "document_title",
            "title",
            "index",
            "extras",
        }
        for key, value in citation.items():
            if key not in known_fields:
                if "extras" not in document_citation:
                    document_citation["extras"] = {}
                document_citation["extras"][key] = value

        return document_citation

    return {
        "type": "non_standard_annotation",
        "value": citation,
    }