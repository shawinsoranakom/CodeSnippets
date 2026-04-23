def soft_nms(boxes_in, Nt_thres=0.3, threshold=0.8, sigma=0.5, method=2):
    """
    soft_nms
    :para boxes_in, N x 9 (coords + score)
    :para threshould, eliminate cases min score(0.001)
    :para Nt_thres, iou_threshi
    :para sigma, gaussian weght
    :method, linear or gaussian
    """
    boxes = boxes_in.copy()
    N = boxes.shape[0]
    if N is None or N < 1:
        return np.array([])
    pos, maxpos = 0, 0
    weight = 0.0
    inds = np.arange(N)
    tbox, sbox = boxes[0].copy(), boxes[0].copy()
    for i in range(N):
        maxscore = boxes[i, 8]
        maxpos = i
        tbox = boxes[i].copy()
        ti = inds[i]
        pos = i + 1
        # get max box
        while pos < N:
            if maxscore < boxes[pos, 8]:
                maxscore = boxes[pos, 8]
                maxpos = pos
            pos = pos + 1
        # add max box as a detection
        boxes[i, :] = boxes[maxpos, :]
        inds[i] = inds[maxpos]
        # swap
        boxes[maxpos, :] = tbox
        inds[maxpos] = ti
        tbox = boxes[i].copy()
        pos = i + 1
        # NMS iteration
        while pos < N:
            sbox = boxes[pos].copy()
            ts_iou_val = intersection(tbox, sbox)
            if ts_iou_val > 0:
                if method == 1:
                    if ts_iou_val > Nt_thres:
                        weight = 1 - ts_iou_val
                    else:
                        weight = 1
                elif method == 2:
                    weight = np.exp(-1.0 * ts_iou_val**2 / sigma)
                else:
                    if ts_iou_val > Nt_thres:
                        weight = 0
                    else:
                        weight = 1
                boxes[pos, 8] = weight * boxes[pos, 8]
                # if box score falls below threshold, discard the box by
                # swapping last box update N
                if boxes[pos, 8] < threshold:
                    boxes[pos, :] = boxes[N - 1, :]
                    inds[pos] = inds[N - 1]
                    N = N - 1
                    pos = pos - 1
            pos = pos + 1

    return boxes[:N]