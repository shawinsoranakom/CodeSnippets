def combine_boxes(icons_bounding_boxes):
        while True:
            combined_boxes = []
            for box in icons_bounding_boxes:
                for i, combined_box in enumerate(combined_boxes):
                    if (
                        box["x"] < combined_box["x"] + combined_box["width"]
                        and box["x"] + box["width"] > combined_box["x"]
                        and box["y"] < combined_box["y"] + combined_box["height"]
                        and box["y"] + box["height"] > combined_box["y"]
                    ):
                        combined_box["x"] = min(box["x"], combined_box["x"])
                        combined_box["y"] = min(box["y"], combined_box["y"])
                        combined_box["width"] = (
                            max(
                                box["x"] + box["width"],
                                combined_box["x"] + combined_box["width"],
                            )
                            - combined_box["x"]
                        )
                        combined_box["height"] = (
                            max(
                                box["y"] + box["height"],
                                combined_box["y"] + combined_box["height"],
                            )
                            - combined_box["y"]
                        )
                        break
                else:
                    combined_boxes.append(box.copy())
            if len(combined_boxes) == len(icons_bounding_boxes):
                break
            else:
                icons_bounding_boxes = combined_boxes
        return combined_boxes