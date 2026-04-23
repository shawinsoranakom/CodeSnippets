def random_crop_flip(self, results):
        image = results["image"]
        polygons = results["polys"]
        ignore_tags = results["ignore_tags"]
        if len(polygons) == 0:
            return results

        if np.random.random() >= self.crop_ratio:
            return results

        h, w, _ = image.shape
        area = h * w
        pad_h = int(h * self.pad_ratio)
        pad_w = int(w * self.pad_ratio)
        h_axis, w_axis = self.generate_crop_target(image, polygons, pad_h, pad_w)
        if len(h_axis) == 0 or len(w_axis) == 0:
            return results

        attempt = 0
        while attempt < 50:
            attempt += 1
            polys_keep = []
            polys_new = []
            ignore_tags_keep = []
            ignore_tags_new = []
            xx = np.random.choice(w_axis, size=2)
            xmin = np.min(xx) - pad_w
            xmax = np.max(xx) - pad_w
            xmin = np.clip(xmin, 0, w - 1)
            xmax = np.clip(xmax, 0, w - 1)
            yy = np.random.choice(h_axis, size=2)
            ymin = np.min(yy) - pad_h
            ymax = np.max(yy) - pad_h
            ymin = np.clip(ymin, 0, h - 1)
            ymax = np.clip(ymax, 0, h - 1)
            if (xmax - xmin) * (ymax - ymin) < area * self.min_area_ratio:
                # area too small
                continue

            pts = np.stack(
                [[xmin, xmax, xmax, xmin], [ymin, ymin, ymax, ymax]]
            ).T.astype(np.int32)
            pp = Polygon(pts)
            fail_flag = False
            for polygon, ignore_tag in zip(polygons, ignore_tags):
                ppi = Polygon(polygon.reshape(-1, 2))
                ppiou, _ = poly_intersection(ppi, pp, buffer=0)
                if (
                    np.abs(ppiou - float(ppi.area)) > self.epsilon
                    and np.abs(ppiou) > self.epsilon
                ):
                    fail_flag = True
                    break
                elif np.abs(ppiou - float(ppi.area)) < self.epsilon:
                    polys_new.append(polygon)
                    ignore_tags_new.append(ignore_tag)
                else:
                    polys_keep.append(polygon)
                    ignore_tags_keep.append(ignore_tag)

            if fail_flag:
                continue
            else:
                break

        cropped = image[ymin:ymax, xmin:xmax, :]
        select_type = np.random.randint(3)
        if select_type == 0:
            img = np.ascontiguousarray(cropped[:, ::-1])
        elif select_type == 1:
            img = np.ascontiguousarray(cropped[::-1, :])
        else:
            img = np.ascontiguousarray(cropped[::-1, ::-1])
        image[ymin:ymax, xmin:xmax, :] = img
        results["img"] = image

        if len(polys_new) != 0:
            height, width, _ = cropped.shape
            if select_type == 0:
                for idx, polygon in enumerate(polys_new):
                    poly = polygon.reshape(-1, 2)
                    poly[:, 0] = width - poly[:, 0] + 2 * xmin
                    polys_new[idx] = poly
            elif select_type == 1:
                for idx, polygon in enumerate(polys_new):
                    poly = polygon.reshape(-1, 2)
                    poly[:, 1] = height - poly[:, 1] + 2 * ymin
                    polys_new[idx] = poly
            else:
                for idx, polygon in enumerate(polys_new):
                    poly = polygon.reshape(-1, 2)
                    poly[:, 0] = width - poly[:, 0] + 2 * xmin
                    poly[:, 1] = height - poly[:, 1] + 2 * ymin
                    polys_new[idx] = poly
            polygons = polys_keep + polys_new
            ignore_tags = ignore_tags_keep + ignore_tags_new
            results["polys"] = np.array(polygons)
            results["ignore_tags"] = ignore_tags

        return results