def get_merge_cells(
        self,
        polygons: np.ndarray,
        rows: Dict,
        row_nums: int,
        col_nums: int,
        longest_col: np.ndarray,
        each_col_widths: List[float],
        each_row_heights: List[float],
    ) -> Dict[int, Dict[int, int]]:
        col_res_merge, row_res_merge = {}, {}
        logic_points = {}
        merge_thresh = 10
        for cur_row, col_list in rows.items():
            one_col_result, one_row_result = {}, {}
            for one_col in col_list:
                box = polygons[one_col]
                box_width = self.compute_L2(box[3, :], box[0, :])

                # 不一定是从0开始的，应该综合已有值和x坐标位置来确定起始位置
                loc_col_idx = np.argmin(np.abs(longest_col - box[0, 0]))
                col_start = max(sum(one_col_result.values()), loc_col_idx)

                # 计算合并多少个列方向单元格
                for i in range(col_start, col_nums):
                    col_cum_sum = sum(each_col_widths[col_start : i + 1])
                    if i == col_start and col_cum_sum > box_width:
                        one_col_result[one_col] = 1
                        break
                    elif abs(col_cum_sum - box_width) <= merge_thresh:
                        one_col_result[one_col] = i + 1 - col_start
                        break
                    # 这里必须进行修正，不然会出现超越阈值范围后列交错
                    elif col_cum_sum > box_width:
                        idx = (
                            i
                            if abs(col_cum_sum - box_width)
                            < abs(col_cum_sum - each_col_widths[i] - box_width)
                            else i - 1
                        )
                        one_col_result[one_col] = idx + 1 - col_start
                        break
                else:
                    one_col_result[one_col] = col_nums - col_start
                col_end = one_col_result[one_col] + col_start - 1
                box_height = self.compute_L2(box[1, :], box[0, :])
                row_start = cur_row
                for j in range(row_start, row_nums):
                    row_cum_sum = sum(each_row_heights[row_start : j + 1])
                    # box_height 不确定是几行的高度，所以要逐个试验，找一个最近的几行的高
                    # 如果第一次row_cum_sum就比box_height大，那么意味着？丢失了一行
                    if j == row_start and row_cum_sum > box_height:
                        one_row_result[one_col] = 1
                        break
                    elif abs(box_height - row_cum_sum) <= merge_thresh:
                        one_row_result[one_col] = j + 1 - row_start
                        break
                    # 这里必须进行修正，不然会出现超越阈值范围后行交错
                    elif row_cum_sum > box_height:
                        idx = (
                            j
                            if abs(row_cum_sum - box_height)
                            < abs(row_cum_sum - each_row_heights[j] - box_height)
                            else j - 1
                        )
                        one_row_result[one_col] = idx + 1 - row_start
                        break
                else:
                    one_row_result[one_col] = row_nums - row_start
                row_end = one_row_result[one_col] + row_start - 1
                logic_points[one_col] = np.array(
                    [row_start, row_end, col_start, col_end]
                )
            col_res_merge[cur_row] = one_col_result
            row_res_merge[cur_row] = one_row_result

        res = {}
        for i, (c, r) in enumerate(zip(col_res_merge.values(), row_res_merge.values())):
            res[i] = {k: [cc, r[k]] for k, cc in c.items()}
        return res, logic_points