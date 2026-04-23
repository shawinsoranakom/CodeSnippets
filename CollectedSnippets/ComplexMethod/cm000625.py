def _extract_text_from_content(content: list[dict]) -> str:
    """Extract plain text from document content structure."""
    text_parts = []
    for element in content:
        if "paragraph" in element:
            for elem in element["paragraph"].get("elements", []):
                if "textRun" in elem:
                    text_parts.append(elem["textRun"].get("content", ""))
        elif "table" in element:
            for row in element["table"].get("tableRows", []):
                for cell in row.get("tableCells", []):
                    cell_content = cell.get("content", [])
                    text_parts.append(_extract_text_from_content(cell_content))
    return "".join(text_parts)