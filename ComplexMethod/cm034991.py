def comps2boundaries(text_comps, comp_pred_labels):
    assert text_comps.ndim == 2
    assert len(text_comps) == len(comp_pred_labels)
    boundaries = []
    if len(text_comps) < 1:
        return boundaries
    for cluster_ind in range(0, int(np.max(comp_pred_labels)) + 1):
        cluster_comp_inds = np.where(comp_pred_labels == cluster_ind)
        text_comp_boxes = (
            text_comps[cluster_comp_inds, :8].reshape((-1, 4, 2)).astype(np.int32)
        )
        score = np.mean(text_comps[cluster_comp_inds, -1])

        if text_comp_boxes.shape[0] < 1:
            continue

        elif text_comp_boxes.shape[0] > 1:
            centers = np.mean(text_comp_boxes, axis=1).astype(np.int32).tolist()
            shortest_path = min_connect_path(centers)
            text_comp_boxes = text_comp_boxes[shortest_path]
            top_line = (
                np.mean(text_comp_boxes[:, 0:2, :], axis=1).astype(np.int32).tolist()
            )
            bot_line = (
                np.mean(text_comp_boxes[:, 2:4, :], axis=1).astype(np.int32).tolist()
            )
            top_line, bot_line = fix_corner(
                top_line, bot_line, text_comp_boxes[0], text_comp_boxes[-1]
            )
            boundary_points = top_line + bot_line[::-1]

        else:
            top_line = text_comp_boxes[0, 0:2, :].astype(np.int32).tolist()
            bot_line = text_comp_boxes[0, 2:4:-1, :].astype(np.int32).tolist()
            boundary_points = top_line + bot_line

        boundary = [p for coord in boundary_points for p in coord] + [score]
        boundaries.append(boundary)

    return boundaries