def detect_sast(
        self,
        tcl_map,
        tvo_map,
        tbo_map,
        tco_map,
        ratio_w,
        ratio_h,
        src_w,
        src_h,
        shrink_ratio_of_width=0.3,
        tcl_map_thresh=0.5,
        offset_expand=1.0,
        out_strid=4.0,
    ):
        """
        first resize the tcl_map, tvo_map and tbo_map to the input_size, then restore the polys
        """
        # restore quad
        scores, quads, xy_text = self.restore_quad(tcl_map, tcl_map_thresh, tvo_map)
        dets = np.hstack((quads, scores)).astype(np.float32, copy=False)
        dets = self.nms(dets)
        if dets.shape[0] == 0:
            return []
        quads = dets[:, :-1].reshape(-1, 4, 2)

        # Compute quad area
        quad_areas = []
        for quad in quads:
            quad_areas.append(-self.quad_area(quad))

        # instance segmentation
        # instance_count, instance_label_map = cv2.connectedComponents(tcl_map.astype(np.uint8), connectivity=8)
        instance_count, instance_label_map = self.cluster_by_quads_tco(
            tcl_map, tcl_map_thresh, quads, tco_map
        )

        # restore single poly with tcl instance.
        poly_list = []
        for instance_idx in range(1, instance_count):
            xy_text = np.argwhere(instance_label_map == instance_idx)[:, ::-1]
            quad = quads[instance_idx - 1]
            q_area = quad_areas[instance_idx - 1]
            if q_area < 5:
                continue

            #
            len1 = float(np.linalg.norm(quad[0] - quad[1]))
            len2 = float(np.linalg.norm(quad[1] - quad[2]))
            min_len = min(len1, len2)
            if min_len < 3:
                continue

            # filter small CC
            if xy_text.shape[0] <= 0:
                continue

            # filter low confidence instance
            xy_text_scores = tcl_map[xy_text[:, 1], xy_text[:, 0], 0]
            if np.sum(xy_text_scores) / quad_areas[instance_idx - 1] < 0.1:
                # if np.sum(xy_text_scores) / quad_areas[instance_idx - 1] < 0.05:
                continue

            # sort xy_text
            left_center_pt = np.array(
                [[(quad[0, 0] + quad[-1, 0]) / 2.0, (quad[0, 1] + quad[-1, 1]) / 2.0]]
            )  # (1, 2)
            right_center_pt = np.array(
                [[(quad[1, 0] + quad[2, 0]) / 2.0, (quad[1, 1] + quad[2, 1]) / 2.0]]
            )  # (1, 2)
            proj_unit_vec = (right_center_pt - left_center_pt) / (
                np.linalg.norm(right_center_pt - left_center_pt) + 1e-6
            )
            proj_value = np.sum(xy_text * proj_unit_vec, axis=1)
            xy_text = xy_text[np.argsort(proj_value)]

            # Sample pts in tcl map
            if self.sample_pts_num == 0:
                sample_pts_num = self.estimate_sample_pts_num(quad, xy_text)
            else:
                sample_pts_num = self.sample_pts_num
            xy_center_line = xy_text[
                np.linspace(
                    0,
                    xy_text.shape[0] - 1,
                    sample_pts_num,
                    endpoint=True,
                    dtype=np.float32,
                ).astype(np.int32)
            ]

            point_pair_list = []
            for x, y in xy_center_line:
                # get corresponding offset
                offset = tbo_map[y, x, :].reshape(2, 2)
                if offset_expand != 1.0:
                    offset_length = np.linalg.norm(offset, axis=1, keepdims=True)
                    expand_length = np.clip(
                        offset_length * (offset_expand - 1), a_min=0.5, a_max=3.0
                    )
                    offset_detal = offset / offset_length * expand_length
                    offset = offset + offset_detal
                    # original point
                ori_yx = np.array([y, x], dtype=np.float32)
                point_pair = (
                    (ori_yx + offset)[:, ::-1]
                    * out_strid
                    / np.array([ratio_w, ratio_h]).reshape(-1, 2)
                )
                point_pair_list.append(point_pair)

            # ndarry: (x, 2), expand poly along width
            detected_poly = self.point_pair2poly(point_pair_list)
            detected_poly = self.expand_poly_along_width(
                detected_poly, shrink_ratio_of_width
            )
            detected_poly[:, 0] = np.clip(detected_poly[:, 0], a_min=0, a_max=src_w)
            detected_poly[:, 1] = np.clip(detected_poly[:, 1], a_min=0, a_max=src_h)
            poly_list.append(detected_poly)

        return poly_list