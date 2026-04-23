def _convert_annotation_to_v1(annotation: dict[str, Any]) -> types.Annotation:
    annotation_type = annotation.get("type")

    if annotation_type == "url_citation":
        known_fields = {
            "type",
            "url",
            "title",
            "cited_text",
            "start_index",
            "end_index",
        }
        url_citation = cast("types.Citation", {})
        for field in ("end_index", "start_index", "title"):
            if field in annotation:
                url_citation[field] = annotation[field]
        url_citation["type"] = "citation"
        url_citation["url"] = annotation["url"]
        for field, value in annotation.items():
            if field not in known_fields:
                if "extras" not in url_citation:
                    url_citation["extras"] = {}
                url_citation["extras"][field] = value
        return url_citation

    if annotation_type == "file_citation":
        known_fields = {
            "type",
            "title",
            "cited_text",
            "start_index",
            "end_index",
            "filename",
        }
        document_citation: types.Citation = {"type": "citation"}
        if "filename" in annotation:
            document_citation["title"] = annotation["filename"]
        for field, value in annotation.items():
            if field not in known_fields:
                if "extras" not in document_citation:
                    document_citation["extras"] = {}
                document_citation["extras"][field] = value

        return document_citation

    # TODO: standardise container_file_citation?
    non_standard_annotation: types.NonStandardAnnotation = {
        "type": "non_standard_annotation",
        "value": annotation,
    }
    return non_standard_annotation