def org_tcl_rois(batch_size, pos_lists, pos_masks, label_lists, tcl_bs):
    """ """
    pos_lists_, pos_masks_, label_lists_ = [], [], []
    img_bs = batch_size
    ngpu = int(batch_size / img_bs)
    img_ids = np.array(pos_lists, dtype=np.int32)[:, 0, 0].copy()
    pos_lists_split, pos_masks_split, label_lists_split = [], [], []
    for i in range(ngpu):
        pos_lists_split.append([])
        pos_masks_split.append([])
        label_lists_split.append([])

    for i in range(img_ids.shape[0]):
        img_id = img_ids[i]
        gpu_id = int(img_id / img_bs)
        img_id = img_id % img_bs
        pos_list = pos_lists[i].copy()
        pos_list[:, 0] = img_id
        pos_lists_split[gpu_id].append(pos_list)
        pos_masks_split[gpu_id].append(pos_masks[i].copy())
        label_lists_split[gpu_id].append(copy.deepcopy(label_lists[i]))
    # repeat or delete
    for i in range(ngpu):
        vp_len = len(pos_lists_split[i])
        if vp_len <= tcl_bs:
            for j in range(0, tcl_bs - vp_len):
                pos_list = pos_lists_split[i][j].copy()
                pos_lists_split[i].append(pos_list)
                pos_mask = pos_masks_split[i][j].copy()
                pos_masks_split[i].append(pos_mask)
                label_list = copy.deepcopy(label_lists_split[i][j])
                label_lists_split[i].append(label_list)
        else:
            for j in range(0, vp_len - tcl_bs):
                c_len = len(pos_lists_split[i])
                pop_id = np.random.permutation(c_len)[0]
                pos_lists_split[i].pop(pop_id)
                pos_masks_split[i].pop(pop_id)
                label_lists_split[i].pop(pop_id)
    # merge
    for i in range(ngpu):
        pos_lists_.extend(pos_lists_split[i])
        pos_masks_.extend(pos_masks_split[i])
        label_lists_.extend(label_lists_split[i])
    return pos_lists_, pos_masks_, label_lists_