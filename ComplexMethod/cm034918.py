def propose_comps_and_attribs(
        self,
        text_region_map,
        center_region_map,
        top_height_map,
        bot_height_map,
        sin_map,
        cos_map,
    ):
        """Generate text components and attributes.

        Args:
            text_region_map (ndarray): The predicted text region probability
                map.
            center_region_map (ndarray): The predicted text center region
                probability map.
            top_height_map (ndarray): The predicted text height map from each
                pixel in text center region to top sideline.
            bot_height_map (ndarray): The predicted text height map from each
                pixel in text center region to bottom sideline.
            sin_map (ndarray): The predicted sin(theta) map.
            cos_map (ndarray): The predicted cos(theta) map.

        Returns:
            comp_attribs (ndarray): The text component attributes.
            text_comps (ndarray): The text components.
        """

        assert (
            text_region_map.shape
            == center_region_map.shape
            == top_height_map.shape
            == bot_height_map.shape
            == sin_map.shape
            == cos_map.shape
        )
        text_mask = text_region_map > self.text_region_thr
        center_region_mask = (center_region_map > self.center_region_thr) * text_mask

        scale = np.sqrt(1.0 / (sin_map**2 + cos_map**2 + 1e-8))
        sin_map, cos_map = sin_map * scale, cos_map * scale

        center_region_mask = fill_hole(center_region_mask)
        center_region_contours, _ = cv2.findContours(
            center_region_mask.astype(np.uint8), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )

        mask_sz = center_region_map.shape
        comp_list = []
        for contour in center_region_contours:
            current_center_mask = np.zeros(mask_sz)
            cv2.drawContours(current_center_mask, [contour], -1, 1, -1)
            if current_center_mask.sum() <= self.center_region_area_thr:
                continue
            score_map = text_region_map * current_center_mask

            text_comps = self.propose_comps(
                score_map,
                top_height_map,
                bot_height_map,
                sin_map,
                cos_map,
                self.comp_score_thr,
                self.min_width,
                self.max_width,
                self.comp_shrink_ratio,
                self.comp_w_h_ratio,
            )

            text_comps = la_nms(text_comps, self.nms_thr)
            text_comp_mask = np.zeros(mask_sz)
            text_comp_boxes = text_comps[:, :8].reshape((-1, 4, 2)).astype(np.int32)

            cv2.drawContours(text_comp_mask, text_comp_boxes, -1, 1, -1)
            if (text_comp_mask * text_mask).sum() < text_comp_mask.sum() * 0.5:
                continue
            if text_comps.shape[-1] > 0:
                comp_list.append(text_comps)

        if len(comp_list) <= 0:
            return None, None

        text_comps = np.vstack(comp_list)
        text_comp_boxes = text_comps[:, :8].reshape((-1, 4, 2))
        centers = np.mean(text_comp_boxes, axis=1).astype(np.int32)
        x = centers[:, 0]
        y = centers[:, 1]

        scores = []
        for text_comp_box in text_comp_boxes:
            text_comp_box[:, 0] = np.clip(text_comp_box[:, 0], 0, mask_sz[1] - 1)
            text_comp_box[:, 1] = np.clip(text_comp_box[:, 1], 0, mask_sz[0] - 1)
            min_coord = np.min(text_comp_box, axis=0).astype(np.int32)
            max_coord = np.max(text_comp_box, axis=0).astype(np.int32)
            text_comp_box = text_comp_box - min_coord
            box_sz = max_coord - min_coord + 1
            temp_comp_mask = np.zeros((box_sz[1], box_sz[0]), dtype=np.uint8)
            cv2.fillPoly(temp_comp_mask, [text_comp_box.astype(np.int32)], 1)
            temp_region_patch = text_region_map[
                min_coord[1] : (max_coord[1] + 1), min_coord[0] : (max_coord[0] + 1)
            ]
            score = cv2.mean(temp_region_patch, temp_comp_mask)[0]
            scores.append(score)
        scores = np.array(scores).reshape((-1, 1))
        text_comps = np.hstack([text_comps[:, :-1], scores])

        h = top_height_map[y, x].reshape((-1, 1)) + bot_height_map[y, x].reshape(
            (-1, 1)
        )
        w = np.clip(h * self.comp_w_h_ratio, self.min_width, self.max_width)
        sin = sin_map[y, x].reshape((-1, 1))
        cos = cos_map[y, x].reshape((-1, 1))

        x = x.reshape((-1, 1))
        y = y.reshape((-1, 1))
        comp_attribs = np.hstack([x, y, h, w, cos, sin])

        return comp_attribs, text_comps