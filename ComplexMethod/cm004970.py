def _extract_polygon_points_by_masks(self, boxes, masks, scale_ratio):
        scale_width, scale_height = scale_ratio[0] / 4, scale_ratio[1] / 4
        mask_height, mask_width = masks.shape[1:]
        polygon_points = []

        for i in range(len(boxes)):
            x_min, y_min, x_max, y_max = boxes[i].astype(np.int32)
            box_w, box_h = x_max - x_min, y_max - y_min

            # default rect
            rect = np.array(
                [[x_min, y_min], [x_max, y_min], [x_max, y_max], [x_min, y_max]],
                dtype=np.float32,
            )

            if box_w <= 0 or box_h <= 0:
                polygon_points.append(rect)
                continue

            # crop mask
            x_coordinates = [int(round((x_min * scale_width).item())), int(round((x_max * scale_width).item()))]
            x_start, x_end = np.clip(x_coordinates, 0, mask_width)
            y_coordinates = [int(round((y_min * scale_height).item())), int(round((y_max * scale_height).item()))]
            y_start, y_end = np.clip(y_coordinates, 0, mask_height)
            cropped_mask = masks[i, y_start:y_end, x_start:x_end]
            if cropped_mask.size == 0 or np.sum(cropped_mask) == 0:
                polygon_points.append(rect)
                continue

            # resize mask to match box size
            resized_mask = cv2.resize(cropped_mask.astype(np.uint8), (box_w, box_h), interpolation=cv2.INTER_NEAREST)

            polygon = self._mask2polygon(resized_mask)
            if polygon is not None and len(polygon) < 4:
                polygon_points.append(rect)
                continue
            if polygon is not None and len(polygon) > 0:
                polygon = polygon + np.array([x_min, y_min])

            polygon_points.append(polygon)

        return polygon_points