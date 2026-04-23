def elem_list_from_xml_tree(xml_path: Path, useless_list: list[str], min_dist: int) -> list[AndroidElement]:
    clickable_list = []
    focusable_list = []
    traverse_xml_tree(xml_path, clickable_list, "clickable", True)
    traverse_xml_tree(xml_path, focusable_list, "focusable", True)
    elem_list = []
    for elem in clickable_list:
        if elem.uid in useless_list:
            continue
        elem_list.append(elem)
    for elem in focusable_list:
        if elem.uid in useless_list:
            continue
        bbox = elem.bbox
        center = (bbox[0][0] + bbox[1][0]) // 2, (bbox[0][1] + bbox[1][1]) // 2
        close = False
        for e in clickable_list:
            bbox = e.bbox
            center_ = (bbox[0][0] + bbox[1][0]) // 2, (bbox[0][1] + bbox[1][1]) // 2
            dist = (abs(center[0] - center_[0]) ** 2 + abs(center[1] - center_[1]) ** 2) ** 0.5
            if dist <= min_dist:
                close = True
                break
        if not close:
            elem_list.append(elem)
    return elem_list