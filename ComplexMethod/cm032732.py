def _extract_raw_positions(item):
    positions = item.get(PDF_POSITIONS_KEY)
    if isinstance(positions, list):
        return deepcopy(positions)

    positions = item.get("positions")
    if isinstance(positions, list):
        return deepcopy(positions)

    position_tag = item.get("position_tag")
    if isinstance(position_tag, str) and position_tag:
        return [[pos[0][-1], *pos[1:]] for pos in RAGFlowPdfParser.extract_positions(position_tag)]

    position_int = item.get("position_int")
    if isinstance(position_int, list):
        return [
            list(pos)
            for pos in position_int
            if isinstance(pos, (list, tuple)) and len(pos) >= 5
        ]

    if item.get("page_number") is not None and all(
        item.get(key) is not None for key in ["x0", "x1", "top", "bottom"]
    ):
        return [[item["page_number"], item["x0"], item["x1"], item["top"], item["bottom"]]]

    return []