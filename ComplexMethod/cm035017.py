def __call__(self, data):
        image = data["image"]
        text_polys = data["polys"]
        ignore_tags = data["ignore_tags"]

        h, w = image.shape[:2]
        text_polys, ignore_tags = self.validate_polygons(text_polys, ignore_tags, h, w)
        gt = np.zeros((h, w), dtype=np.float32)
        mask = np.ones((h, w), dtype=np.float32)
        for i in range(len(text_polys)):
            polygon = text_polys[i]
            height = max(polygon[:, 1]) - min(polygon[:, 1])
            width = max(polygon[:, 0]) - min(polygon[:, 0])
            if ignore_tags[i] or min(height, width) < self.min_text_size:
                cv2.fillPoly(mask, polygon.astype(np.int32)[np.newaxis, :, :], 0)
                ignore_tags[i] = True
            else:
                polygon_shape = Polygon(polygon)
                subject = [tuple(l) for l in polygon]
                padding = pyclipper.PyclipperOffset()
                padding.AddPath(subject, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
                shrunk = []

                # Increase the shrink ratio every time we get multiple polygon returned back
                possible_ratios = np.arange(self.shrink_ratio, 1, self.shrink_ratio)
                np.append(possible_ratios, 1)
                # print(possible_ratios)
                for ratio in possible_ratios:
                    # print(f"Change shrink ratio to {ratio}")
                    distance = (
                        polygon_shape.area
                        * (1 - np.power(ratio, 2))
                        / polygon_shape.length
                    )
                    shrunk = padding.Execute(-distance)
                    if len(shrunk) == 1:
                        break

                if shrunk == []:
                    cv2.fillPoly(mask, polygon.astype(np.int32)[np.newaxis, :, :], 0)
                    ignore_tags[i] = True
                    continue

                for each_shrink in shrunk:
                    shrink = np.array(each_shrink).reshape(-1, 2)
                    cv2.fillPoly(gt, [shrink.astype(np.int32)], 1)

        data["shrink_map"] = gt
        data["shrink_mask"] = mask
        return data