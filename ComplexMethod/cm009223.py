def _convert_annotation_from_v1(annotation: types.Annotation) -> dict[str, Any]:
    """Convert LangChain annotation format to Anthropic's native citation format."""
    if annotation["type"] == "non_standard_annotation":
        return annotation["value"]

    if annotation["type"] == "citation":
        if "url" in annotation:
            # web_search_result_location
            out: dict[str, Any] = {}
            if cited_text := annotation.get("cited_text"):
                out["cited_text"] = cited_text
            if "encrypted_index" in annotation.get("extras", {}):
                out["encrypted_index"] = annotation.get("extras", {})["encrypted_index"]
            if "title" in annotation:
                out["title"] = annotation["title"]
            out["type"] = "web_search_result_location"
            out["url"] = annotation.get("url")

            for key, value in annotation.get("extras", {}).items():
                if key not in out:
                    out[key] = value

            return out

        if "start_char_index" in annotation.get("extras", {}):
            # char_location
            out = {"type": "char_location"}
            for field in ["cited_text"]:
                if value := annotation.get(field):
                    out[field] = value
            if title := annotation.get("title"):
                out["document_title"] = title

            for key, value in annotation.get("extras", {}).items():
                out[key] = value
            out = {k: out[k] for k in sorted(out)}

            return out

        if "search_result_index" in annotation.get("extras", {}):
            # search_result_location
            out = {"type": "search_result_location"}
            for field in ["cited_text", "title"]:
                if value := annotation.get(field):
                    out[field] = value

            for key, value in annotation.get("extras", {}).items():
                out[key] = value

            return out

        if "start_block_index" in annotation.get("extras", {}):
            # content_block_location
            out = {}
            if cited_text := annotation.get("cited_text"):
                out["cited_text"] = cited_text
            if "document_index" in annotation.get("extras", {}):
                out["document_index"] = annotation.get("extras", {})["document_index"]
            if "title" in annotation:
                out["document_title"] = annotation["title"]

            for key, value in annotation.get("extras", {}).items():
                if key not in out:
                    out[key] = value

            out["type"] = "content_block_location"
            return out

        if "start_page_number" in annotation.get("extras", {}):
            # page_location
            out = {"type": "page_location"}
            for field in ["cited_text"]:
                if value := annotation.get(field):
                    out[field] = value
            if title := annotation.get("title"):
                out["document_title"] = title

            for key, value in annotation.get("extras", {}).items():
                out[key] = value

            return out

        return cast(dict[str, Any], annotation)

    return cast(dict[str, Any], annotation)