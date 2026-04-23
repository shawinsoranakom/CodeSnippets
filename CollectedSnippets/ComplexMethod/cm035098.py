def pre_process(
    label_list, pos_list, pos_mask, max_text_length, max_text_nums, pad_num, tcl_bs
):
    label_list = label_list.numpy()
    batch, _, _, _ = label_list.shape
    pos_list = pos_list.numpy()
    pos_mask = pos_mask.numpy()
    pos_list_t = []
    pos_mask_t = []
    label_list_t = []
    for i in range(batch):
        for j in range(max_text_nums):
            if pos_mask[i, j].any():
                pos_list_t.append(pos_list[i][j])
                pos_mask_t.append(pos_mask[i][j])
                label_list_t.append(label_list[i][j])
    pos_list, pos_mask, label_list = org_tcl_rois(
        batch, pos_list_t, pos_mask_t, label_list_t, tcl_bs
    )
    label = []
    tt = [l.tolist() for l in label_list]
    for i in range(tcl_bs):
        k = 0
        for j in range(max_text_length):
            if tt[i][j][0] != pad_num:
                k += 1
            else:
                break
        label.append(k)
    label = paddle.to_tensor(label)
    label = paddle.cast(label, dtype="int64")
    pos_list = paddle.to_tensor(pos_list)
    pos_mask = paddle.to_tensor(pos_mask)
    label_list = paddle.squeeze(paddle.to_tensor(label_list), axis=2)
    label_list = paddle.cast(label_list, dtype="int32")
    return pos_list, pos_mask, label_list, label