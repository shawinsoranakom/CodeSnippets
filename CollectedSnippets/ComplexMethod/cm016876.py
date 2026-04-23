def fillConvexPoly(canvas_np, pts, color, **kwargs):
        """Fill polygon using vectorized scanline algorithm."""
        if len(pts) < 3:
            return
        pts = np.array(pts, dtype=np.int32)
        h, w = canvas_np.shape[:2]
        y_min, y_max, x_min, x_max = max(0, pts[:, 1].min()), min(h, pts[:, 1].max() + 1), max(0, pts[:, 0].min()), min(w, pts[:, 0].max() + 1)
        if y_max <= y_min or x_max <= x_min:
            return
        yy, xx = np.mgrid[y_min:y_max, x_min:x_max]
        mask = np.zeros((y_max - y_min, x_max - x_min), dtype=bool)

        for i in range(len(pts)):
            p1, p2 = pts[i], pts[(i + 1) % len(pts)]
            y1, y2 = p1[1], p2[1]
            if y1 == y2:
                continue
            if y1 > y2:
                p1, p2, y1, y2 = p2, p1, p2[1], p1[1]
            if not (edge_mask := (yy >= y1) & (yy < y2)).any():
                continue
            mask ^= edge_mask & (xx >= p1[0] + (yy - y1) * (p2[0] - p1[0]) / (y2 - y1))

        canvas_np[y_min:y_max, x_min:x_max][mask] = color