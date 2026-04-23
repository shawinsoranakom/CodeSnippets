def sample_points_on_bbox(self, line, n=50):
        assert line.ndim == 2
        assert line.shape[0] >= 2
        assert line.shape[1] == 2
        assert isinstance(n, int)
        assert n > 0

        length_list = [norm(line[i + 1] - line[i]) for i in range(len(line) - 1)]
        total_length = sum(length_list)
        mean_length = total_length / (len(length_list) + 1e-8)
        group = [[0]]
        for i in range(len(length_list)):
            point_id = i + 1
            if length_list[i] < 0.9 * mean_length:
                for g in group:
                    if i in g:
                        g.append(point_id)
                        break
            else:
                g = [point_id]
                group.append(g)

        top_tail_len = norm(line[0] - line[-1])
        if top_tail_len < 0.9 * mean_length:
            group[0].extend(g)
            group.remove(g)
        mean_positions = []
        for indices in group:
            x_sum = 0
            y_sum = 0
            for index in indices:
                x, y = line[index]
                x_sum += x
                y_sum += y
            num_points = len(indices)
            mean_x = x_sum / num_points
            mean_y = y_sum / num_points
            mean_positions.append((mean_x, mean_y))
        resampled_line = np.array(mean_positions)
        return resampled_line