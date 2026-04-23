def find_head_tail(
        self, points: np.ndarray, orientation_thr: float
    ) -> Tuple[list, list]:
        assert points.ndim == 2
        assert points.shape[0] >= 4
        assert points.shape[1] == 2
        assert isinstance(orientation_thr, float)

        if len(points) > 4:
            pad_points = np.vstack([points, points[0]])
            edge_vec = pad_points[1:] - pad_points[:-1]

            theta_sum = []
            adjacent_vec_theta = []
            for i, edge_vec1 in enumerate(edge_vec):
                adjacent_ind = [x % len(edge_vec) for x in [i - 1, i + 1]]
                adjacent_edge_vec = edge_vec[adjacent_ind]
                temp_theta_sum = np.sum(self.vector_angle(edge_vec1, adjacent_edge_vec))
                temp_adjacent_theta = self.vector_angle(
                    adjacent_edge_vec[0], adjacent_edge_vec[1]
                )
                theta_sum.append(temp_theta_sum)
                adjacent_vec_theta.append(temp_adjacent_theta)
            theta_sum_score = np.array(theta_sum) / np.pi
            adjacent_theta_score = np.array(adjacent_vec_theta) / np.pi
            poly_center = np.mean(points, axis=0)
            edge_dist = np.maximum(
                norm(pad_points[1:] - poly_center, axis=-1),
                norm(pad_points[:-1] - poly_center, axis=-1),
            )
            dist_score = edge_dist / np.max(edge_dist)
            position_score = np.zeros(len(edge_vec))
            score = 0.5 * theta_sum_score + 0.15 * adjacent_theta_score
            score += 0.35 * dist_score
            if len(points) % 2 == 0:
                position_score[(len(score) // 2 - 1)] += 1
                position_score[-1] += 1
            score += 0.1 * position_score
            pad_score = np.concatenate([score, score])
            score_matrix = np.zeros((len(score), len(score) - 3))
            x = np.arange(len(score) - 3) / float(len(score) - 4)
            gaussian = (
                1.0
                / (np.sqrt(2.0 * np.pi) * 0.5)
                * np.exp(-np.power((x - 0.5) / 0.5, 2.0) / 2)
            )
            gaussian = gaussian / np.max(gaussian)
            for i in range(len(score)):
                score_matrix[i, :] = (
                    score[i]
                    + pad_score[(i + 2) : (i + len(score) - 1)] * gaussian * 0.3
                )

            head_start, tail_increment = np.unravel_index(
                score_matrix.argmax(), score_matrix.shape
            )
            tail_start = (head_start + tail_increment + 2) % len(points)
            head_end = (head_start + 1) % len(points)
            tail_end = (tail_start + 1) % len(points)

            if head_end > tail_end:
                head_start, tail_start = tail_start, head_start
                head_end, tail_end = tail_end, head_end
            head_inds = [head_start, head_end]
            tail_inds = [tail_start, tail_end]
        else:
            if self.vector_slope(points[1] - points[0]) + self.vector_slope(
                points[3] - points[2]
            ) < self.vector_slope(points[2] - points[1]) + self.vector_slope(
                points[0] - points[3]
            ):
                horizontal_edge_inds = [[0, 1], [2, 3]]
                vertical_edge_inds = [[3, 0], [1, 2]]
            else:
                horizontal_edge_inds = [[3, 0], [1, 2]]
                vertical_edge_inds = [[0, 1], [2, 3]]

            vertical_len_sum = norm(
                points[vertical_edge_inds[0][0]] - points[vertical_edge_inds[0][1]]
            ) + norm(
                points[vertical_edge_inds[1][0]] - points[vertical_edge_inds[1][1]]
            )
            horizontal_len_sum = norm(
                points[horizontal_edge_inds[0][0]] - points[horizontal_edge_inds[0][1]]
            ) + norm(
                points[horizontal_edge_inds[1][0]] - points[horizontal_edge_inds[1][1]]
            )

            if vertical_len_sum > horizontal_len_sum * orientation_thr:
                head_inds = horizontal_edge_inds[0]
                tail_inds = horizontal_edge_inds[1]
            else:
                head_inds = vertical_edge_inds[0]
                tail_inds = vertical_edge_inds[1]

        return head_inds, tail_inds