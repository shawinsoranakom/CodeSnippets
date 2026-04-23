def ellipse2Poly(center, axes, angle, arc_start, arc_end, delta=1, **kwargs):
        """Python implementation of cv2.ellipse2Poly."""
        axes = (axes[0] + 0.5, axes[1] + 0.5) # to better match cv2 output
        angle = angle % 360
        if arc_start > arc_end:
            arc_start, arc_end = arc_end, arc_start
        while arc_start < 0:
            arc_start, arc_end = arc_start + 360, arc_end + 360
        while arc_end > 360:
            arc_end, arc_start = arc_end - 360, arc_start - 360
        if arc_end - arc_start > 360:
            arc_start, arc_end = 0, 360

        angle_rad = math.radians(angle)
        alpha, beta = math.cos(angle_rad), math.sin(angle_rad)
        pts = []
        for i in range(arc_start, arc_end + delta, delta):
            theta_rad = math.radians(min(i, arc_end))
            x, y = axes[0] * math.cos(theta_rad), axes[1] * math.sin(theta_rad)
            pts.append([int(round(center[0] + x * alpha - y * beta)), int(round(center[1] + x * beta + y * alpha))])

        unique_pts, prev_pt = [], (float('inf'), float('inf'))
        for pt in pts:
            if (pt_tuple := tuple(pt)) != prev_pt:
                unique_pts.append(pt)
                prev_pt = pt_tuple

        return unique_pts if len(unique_pts) > 1 else [[center[0], center[1]], [center[0], center[1]]]