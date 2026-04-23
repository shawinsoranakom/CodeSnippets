def sorted_ocr_boxes(
    dt_boxes: Union[np.ndarray, list], threhold: float = 0.2
) -> Tuple[Union[np.ndarray, list], List[int]]:
    """
    Sort text boxes in order from top to bottom, left to right
    args:
        dt_boxes(array):detected text boxes with (xmin, ymin, xmax, ymax)
    return:
        sorted boxes(array) with (xmin, ymin, xmax, ymax)
    """
    num_boxes = len(dt_boxes)
    if num_boxes <= 0:
        return dt_boxes, []
    indexed_boxes = [(box, idx) for idx, box in enumerate(dt_boxes)]
    sorted_boxes_with_idx = sorted(indexed_boxes, key=lambda x: (x[0][1], x[0][0]))
    _boxes, indices = zip(*sorted_boxes_with_idx)
    indices = list(indices)
    _boxes = [dt_boxes[i] for i in indices]
    threahold = 20
    # 避免输出和输入格式不对应，与函数功能不符合
    if isinstance(dt_boxes, np.ndarray):
        _boxes = np.array(_boxes)
    for i in range(num_boxes - 1):
        for j in range(i, -1, -1):
            c_idx = is_single_axis_contained(
                _boxes[j], _boxes[j + 1], axis="y", threhold=threhold
            )
            if (
                c_idx is not None
                and _boxes[j + 1][0] < _boxes[j][0]
                and abs(_boxes[j][1] - _boxes[j + 1][1]) < threahold
            ):
                _boxes[j], _boxes[j + 1] = _boxes[j + 1].copy(), _boxes[j].copy()
                indices[j], indices[j + 1] = indices[j + 1], indices[j]
            else:
                break
    return _boxes, indices