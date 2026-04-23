def line(canvas_np, pt1, pt2, color, thickness=1, **kwargs):
        """Draw line using Bresenham's algorithm with NumPy operations."""
        x0, y0, x1, y1 = *pt1, *pt2
        h, w = canvas_np.shape[:2]
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err, x, y, line_points = dx - dy, x0, y0, []

        while True:
            line_points.append((x, y))
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err, x = err - dy, x + sx
            if e2 < dx:
                err, y = err + dx, y + sy

        if thickness > 1:
            radius, radius_int = (thickness / 2.0) + 0.5, int(np.ceil((thickness / 2.0) + 0.5))
            for px, py in line_points:
                y_min, y_max, x_min, x_max = max(0, py - radius_int), min(h, py + radius_int + 1), max(0, px - radius_int), min(w, px + radius_int + 1)
                if y_max > y_min and x_max > x_min:
                    yy, xx = np.ogrid[y_min:y_max, x_min:x_max]
                    canvas_np[y_min:y_max, x_min:x_max][(xx - px)**2 + (yy - py)**2 <= radius**2] = color
        else:
            line_points = np.array(line_points)
            valid = (line_points[:, 1] >= 0) & (line_points[:, 1] < h) & (line_points[:, 0] >= 0) & (line_points[:, 0] < w)
            if (valid_points := line_points[valid]).size:
                canvas_np[valid_points[:, 1], valid_points[:, 0]] = color