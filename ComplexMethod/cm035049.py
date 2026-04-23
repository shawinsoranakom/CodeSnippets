def resample_line(self, line, n):
        assert line.ndim == 2
        assert line.shape[0] >= 2
        assert line.shape[1] == 2
        assert isinstance(n, int)
        assert n > 2

        edges_length, total_length = self.cal_curve_length(line)
        t_org = np.insert(np.cumsum(edges_length), 0, 0)
        unit_t = total_length / (n - 1)
        t_equidistant = np.arange(1, n - 1, dtype=np.float32) * unit_t
        edge_ind = 0
        points = [line[0]]
        for t in t_equidistant:
            while edge_ind < len(edges_length) - 1 and t > t_org[edge_ind + 1]:
                edge_ind += 1
            t_l, t_r = t_org[edge_ind], t_org[edge_ind + 1]
            weight = np.array([t_r - t, t - t_l], dtype=np.float32) / (
                t_r - t_l + self.eps
            )
            p_coords = np.dot(weight, line[[edge_ind, edge_ind + 1]])
            points.append(p_coords)
        points.append(line[-1])
        resampled_line = np.vstack(points)

        return resampled_line