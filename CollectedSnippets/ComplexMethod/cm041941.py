def traverse_xml_tree(xml_path: Path, elem_list: list[AndroidElement], attrib: str, add_index=False):
    path = []
    extra_config = config.extra
    for event, elem in iterparse(str(xml_path), ["start", "end"]):
        if event == "start":
            path.append(elem)
            if attrib in elem.attrib and elem.attrib[attrib] == "true":
                parent_prefix = ""
                if len(path) > 1:
                    parent_prefix = get_id_from_element(path[-2])
                bounds = elem.attrib["bounds"][1:-1].split("][")
                x1, y1 = map(int, bounds[0].split(","))
                x2, y2 = map(int, bounds[1].split(","))
                center = (x1 + x2) // 2, (y1 + y2) // 2
                elem_id = get_id_from_element(elem)
                if parent_prefix:
                    elem_id = parent_prefix + "_" + elem_id
                if add_index:
                    elem_id += f"_{elem.attrib['index']}"
                close = False
                for e in elem_list:
                    bbox = e.bbox
                    center_ = (bbox[0][0] + bbox[1][0]) // 2, (bbox[0][1] + bbox[1][1]) // 2
                    dist = (abs(center[0] - center_[0]) ** 2 + abs(center[1] - center_[1]) ** 2) ** 0.5
                    if dist <= extra_config.get("min_dist", 30):
                        close = True
                        break
                if not close:
                    elem_list.append(AndroidElement(uid=elem_id, bbox=((x1, y1), (x2, y2)), attrib=attrib))

        if event == "end":
            path.pop()