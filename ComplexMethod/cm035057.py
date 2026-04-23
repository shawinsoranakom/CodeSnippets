def __call__(self, results):
        image = results["image"]
        polygons = results["polys"]
        ignore_tags = results["ignore_tags"]
        if len(polygons) < 1:
            return results

        if np.random.random_sample() < self.crop_ratio:
            crop_box = self.sample_crop_box(image.shape, results)
            img = self.crop_img(image, crop_box)
            results["image"] = img
            # crop and filter masks
            x1, y1, x2, y2 = crop_box
            w = max(x2 - x1, 1)
            h = max(y2 - y1, 1)
            polygons[:, :, 0::2] = polygons[:, :, 0::2] - x1
            polygons[:, :, 1::2] = polygons[:, :, 1::2] - y1

            valid_masks_list = []
            valid_tags_list = []
            for ind, polygon in enumerate(polygons):
                if (
                    (polygon[:, ::2] > -4).all()
                    and (polygon[:, ::2] < w + 4).all()
                    and (polygon[:, 1::2] > -4).all()
                    and (polygon[:, 1::2] < h + 4).all()
                ):
                    polygon[:, ::2] = np.clip(polygon[:, ::2], 0, w)
                    polygon[:, 1::2] = np.clip(polygon[:, 1::2], 0, h)
                    valid_masks_list.append(polygon)
                    valid_tags_list.append(ignore_tags[ind])

            results["polys"] = np.array(valid_masks_list)
            results["ignore_tags"] = valid_tags_list

        return results