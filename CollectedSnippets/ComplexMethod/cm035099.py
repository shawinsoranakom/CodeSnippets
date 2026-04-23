def instance_ctc_greedy_decoder(
    gather_info, logits_map, pts_num=4, point_gather_mode=None
):
    _, _, C = logits_map.shape
    if point_gather_mode == "align":
        insert_num = 0
        gather_info = np.array(gather_info)
        length = len(gather_info) - 1
        for index in range(length):
            stride_y = np.abs(
                gather_info[index + insert_num][0]
                - gather_info[index + 1 + insert_num][0]
            )
            stride_x = np.abs(
                gather_info[index + insert_num][1]
                - gather_info[index + 1 + insert_num][1]
            )
            max_points = int(max(stride_x, stride_y))
            stride = (
                gather_info[index + insert_num] - gather_info[index + 1 + insert_num]
            ) / (max_points)
            insert_num_temp = max_points - 1

            for i in range(int(insert_num_temp)):
                insert_value = gather_info[index + insert_num] - (i + 1) * stride
                insert_index = index + i + 1 + insert_num
                gather_info = np.insert(gather_info, insert_index, insert_value, axis=0)
            insert_num += insert_num_temp
        gather_info = gather_info.tolist()
    else:
        pass
    ys, xs = zip(*gather_info)
    logits_seq = logits_map[list(ys), list(xs)]
    probs_seq = logits_seq
    labels = np.argmax(probs_seq, axis=1)
    dst_str = [k for k, v_ in groupby(labels) if k != C - 1]
    detal = len(gather_info) // (pts_num - 1)
    keep_idx_list = [0] + [detal * (i + 1) for i in range(pts_num - 2)] + [-1]
    keep_gather_list = [gather_info[idx] for idx in keep_idx_list]
    return dst_str, keep_gather_list