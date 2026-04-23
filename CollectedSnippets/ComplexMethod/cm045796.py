def sample_points_on_bbox_bp(self, line, n=50):
        assert line.ndim == 2
        assert line.shape[0] >= 2
        assert line.shape[1] == 2
        assert isinstance(n, int)
        assert n > 0

        length_list = [norm(line[i + 1] - line[i]) for i in range(len(line) - 1)]
        total_length = sum(length_list)
        length_cumsum = np.cumsum([0.0] + length_list)
        delta_length = total_length / (float(n) + 1e-8)
        current_edge_ind = 0
        resampled_line = [line[0]]

        for i in range(1, n):
            current_line_len = i * delta_length
            while (
                current_edge_ind + 1 < len(length_cumsum)
                and current_line_len >= length_cumsum[current_edge_ind + 1]
            ):
                current_edge_ind += 1
            current_edge_end_shift = current_line_len - length_cumsum[current_edge_ind]
            if current_edge_ind >= len(length_list):
                break
            end_shift_ratio = current_edge_end_shift / length_list[current_edge_ind]
            current_point = (
                line[current_edge_ind]
                + (line[current_edge_ind + 1] - line[current_edge_ind])
                * end_shift_ratio
            )
            resampled_line.append(current_point)
        resampled_line.append(line[-1])
        resampled_line = np.array(resampled_line)
        return resampled_line