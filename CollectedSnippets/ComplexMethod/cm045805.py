def _rectangles_union_area(cls, bboxes: list[tuple[float, float, float, float]]) -> float:
        if not bboxes:
            return 0.0

        xs = sorted({bbox[0] for bbox in bboxes} | {bbox[2] for bbox in bboxes})
        total_area = 0.0

        for idx in range(len(xs) - 1):
            x_left = xs[idx]
            x_right = xs[idx + 1]
            if x_right <= x_left:
                continue

            y_intervals = []
            for bbox in bboxes:
                if bbox[0] < x_right and bbox[2] > x_left:
                    y_intervals.append((bbox[1], bbox[3]))

            if not y_intervals:
                continue

            y_intervals.sort()
            merged_height = 0.0
            current_y0, current_y1 = y_intervals[0]

            for y0, y1 in y_intervals[1:]:
                if y0 <= current_y1:
                    current_y1 = max(current_y1, y1)
                    continue

                merged_height += max(0.0, current_y1 - current_y0)
                current_y0, current_y1 = y0, y1

            merged_height += max(0.0, current_y1 - current_y0)
            total_area += (x_right - x_left) * merged_height

        return total_area