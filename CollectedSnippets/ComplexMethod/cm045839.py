def get_rows(polygons: np.array, rows_thresh=10) -> Dict[int, List[int]]:
        """对每个框进行行分类，框定哪个是一行的"""
        y_axis = polygons[:, 0, 1]
        if y_axis.size == 1:
            return {0: [0]}

        concat_y = np.array(list(zip(y_axis, y_axis[1:])))
        minus_res = concat_y[:, 1] - concat_y[:, 0]

        result = {}
        split_idxs = np.argwhere(abs(minus_res) > rows_thresh).squeeze()
        # 如果都在一行，则将所有下标设置为同一行
        if split_idxs.size == 0:
            return {0: [i for i in range(len(y_axis))]}
        if split_idxs.ndim == 0:
            split_idxs = split_idxs[None, ...]

        if max(split_idxs) != len(minus_res):
            split_idxs = np.append(split_idxs, len(minus_res))

        start_idx = 0
        for row_num, idx in enumerate(split_idxs):
            if row_num != 0:
                start_idx = split_idxs[row_num - 1] + 1
            result.setdefault(row_num, []).extend(range(start_idx, idx + 1))

        # 计算每一行相邻cell的iou，如果大于0.2，则合并为同一个cell
        return result