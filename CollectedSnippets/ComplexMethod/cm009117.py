def _convert_annotation_from_v1(annotation: types.Annotation) -> dict[str, Any]:
    """Convert a v1 `Annotation` to the v0.3 format (for Responses API)."""
    if annotation["type"] == "citation":
        new_ann: dict[str, Any] = {}
        for field in ("end_index", "start_index"):
            if field in annotation:
                new_ann[field] = annotation[field]

        if "url" in annotation:
            # URL citation
            if "title" in annotation:
                new_ann["title"] = annotation["title"]
            new_ann["type"] = "url_citation"
            new_ann["url"] = annotation["url"]

            if extra_fields := annotation.get("extras"):
                new_ann.update(dict(extra_fields.items()))
        else:
            # Document citation
            new_ann["type"] = "file_citation"

            if extra_fields := annotation.get("extras"):
                new_ann.update(dict(extra_fields.items()))

            if "title" in annotation:
                new_ann["filename"] = annotation["title"]

        return new_ann

    if annotation["type"] == "non_standard_annotation":
        return annotation["value"]

    return dict(annotation)