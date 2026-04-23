def sort_and_expand_with_direction_v2(pos_list, f_direction, binary_tcl_map):
    """
    f_direction: h x w x 2
    pos_list: [[y, x], [y, x], [y, x] ...]
    binary_tcl_map: h x w
    """
    h, w, _ = f_direction.shape
    sorted_list, point_direction = sort_with_direction(pos_list, f_direction)

    # expand along
    point_num = len(sorted_list)
    sub_direction_len = max(point_num // 3, 2)
    left_direction = point_direction[:sub_direction_len, :]
    right_dirction = point_direction[point_num - sub_direction_len :, :]

    left_average_direction = -np.mean(left_direction, axis=0, keepdims=True)
    left_average_len = np.linalg.norm(left_average_direction)
    left_start = np.array(sorted_list[0])
    left_step = left_average_direction / (left_average_len + 1e-6)

    right_average_direction = np.mean(right_dirction, axis=0, keepdims=True)
    right_average_len = np.linalg.norm(right_average_direction)
    right_step = right_average_direction / (right_average_len + 1e-6)
    right_start = np.array(sorted_list[-1])

    append_num = max(int((left_average_len + right_average_len) / 2.0 * 0.15), 1)
    max_append_num = 2 * append_num

    left_list = []
    right_list = []
    for i in range(max_append_num):
        ly, lx = (
            np.round(left_start + left_step * (i + 1))
            .flatten()
            .astype("int32")
            .tolist()
        )
        if ly < h and lx < w and (ly, lx) not in left_list:
            if binary_tcl_map[ly, lx] > 0.5:
                left_list.append((ly, lx))
            else:
                break

    for i in range(max_append_num):
        ry, rx = (
            np.round(right_start + right_step * (i + 1))
            .flatten()
            .astype("int32")
            .tolist()
        )
        if ry < h and rx < w and (ry, rx) not in right_list:
            if binary_tcl_map[ry, rx] > 0.5:
                right_list.append((ry, rx))
            else:
                break

    all_list = left_list[::-1] + sorted_list + right_list
    return all_list