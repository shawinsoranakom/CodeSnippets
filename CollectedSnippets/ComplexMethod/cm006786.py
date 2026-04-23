def parse_structured_text(text: str, file_path: str) -> str | dict | list:
    """Parse structured text formats (JSON, YAML, XML) and normalize text.

    Args:
        text: The text content to parse
        file_path: The file path (used to determine format)

    Returns:
        Parsed content (dict/list for JSON, dict for YAML, str for XML)
    """
    if file_path.endswith(".json"):
        loaded_json = orjson.loads(text)
        if isinstance(loaded_json, dict):
            loaded_json = {k: normalize_text(v) if isinstance(v, str) else v for k, v in loaded_json.items()}
        elif isinstance(loaded_json, list):
            loaded_json = [normalize_text(item) if isinstance(item, str) else item for item in loaded_json]
        return orjson.dumps(loaded_json).decode("utf-8")

    if file_path.endswith((".yaml", ".yml")):
        return yaml.safe_load(text)

    if file_path.endswith(".xml"):
        xml_element = ElementTree.fromstring(text)
        return ElementTree.tostring(xml_element, encoding="unicode")

    return text