def merge_fragmented(boxes, x_threshold=10, y_threshold=10):
    merged_boxes = []
    visited = set()

    for i, box1 in enumerate(boxes):
        if i in visited:
            continue

        merged_box = [point[:] for point in box1]

        for j, box2 in enumerate(boxes[i + 1 :], start=i + 1):
            if j not in visited:
                merged_result = merge_boxes(
                    merged_box, box2, x_threshold=x_threshold, y_threshold=y_threshold
                )
                if merged_result:
                    merged_box = merged_result
                    visited.add(j)

        merged_boxes.append(merged_box)

    if len(merged_boxes) == len(boxes):
        return np.array(merged_boxes)
    else:
        return merge_fragmented(merged_boxes, x_threshold, y_threshold)