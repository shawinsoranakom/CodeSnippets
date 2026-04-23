def generate_level_targets(self, img_size, text_polys, ignore_polys):
        """Generate ground truth target on each level.

        Args:
            img_size (list[int]): Shape of input image.
            text_polys (list[list[ndarray]]): A list of ground truth polygons.
            ignore_polys (list[list[ndarray]]): A list of ignored polygons.
        Returns:
            level_maps (list(ndarray)): A list of ground target on each level.
        """
        h, w = img_size
        lv_size_divs = self.level_size_divisors
        lv_proportion_range = self.level_proportion_range
        lv_text_polys = [[] for i in range(len(lv_size_divs))]
        lv_ignore_polys = [[] for i in range(len(lv_size_divs))]
        level_maps = []
        for poly in text_polys:
            polygon = np.array(poly, dtype=np.int32).reshape((1, -1, 2))
            _, _, box_w, box_h = cv2.boundingRect(polygon)
            proportion = max(box_h, box_w) / (h + 1e-8)

            for ind, proportion_range in enumerate(lv_proportion_range):
                if proportion_range[0] < proportion < proportion_range[1]:
                    lv_text_polys[ind].append(poly / lv_size_divs[ind])

        for ignore_poly in ignore_polys:
            polygon = np.array(ignore_poly, dtype=np.int32).reshape((1, -1, 2))
            _, _, box_w, box_h = cv2.boundingRect(polygon)
            proportion = max(box_h, box_w) / (h + 1e-8)

            for ind, proportion_range in enumerate(lv_proportion_range):
                if proportion_range[0] < proportion < proportion_range[1]:
                    lv_ignore_polys[ind].append(ignore_poly / lv_size_divs[ind])

        for ind, size_divisor in enumerate(lv_size_divs):
            current_level_maps = []
            level_img_size = (h // size_divisor, w // size_divisor)

            text_region = self.generate_text_region_mask(
                level_img_size, lv_text_polys[ind]
            )[None]
            current_level_maps.append(text_region)

            center_region = self.generate_center_region_mask(
                level_img_size, lv_text_polys[ind]
            )[None]
            current_level_maps.append(center_region)

            effective_mask = self.generate_effective_mask(
                level_img_size, lv_ignore_polys[ind]
            )[None]
            current_level_maps.append(effective_mask)

            fourier_real_map, fourier_image_maps = self.generate_fourier_maps(
                level_img_size, lv_text_polys[ind]
            )
            current_level_maps.append(fourier_real_map)
            current_level_maps.append(fourier_image_maps)

            level_maps.append(np.concatenate(current_level_maps))

        return level_maps