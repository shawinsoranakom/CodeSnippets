def generate_tcl_ctc_label(
        self,
        h,
        w,
        polys,
        tags,
        text_strs,
        ds_ratio,
        tcl_ratio=0.3,
        shrink_ratio_of_width=0.15,
    ):
        """
        Generate polygon.
        """
        self.ds_ratio = ds_ratio
        score_map_big = np.zeros(
            (
                h,
                w,
            ),
            dtype=np.float32,
        )
        h, w = int(h * ds_ratio), int(w * ds_ratio)
        polys = polys * ds_ratio

        score_map = np.zeros(
            (
                h,
                w,
            ),
            dtype=np.float32,
        )
        score_label_map = np.zeros(
            (
                h,
                w,
            ),
            dtype=np.float32,
        )
        tbo_map = np.zeros((h, w, 5), dtype=np.float32)
        training_mask = np.ones(
            (
                h,
                w,
            ),
            dtype=np.float32,
        )
        direction_map = np.ones((h, w, 3)) * np.array([0, 0, 1]).reshape(
            [1, 1, 3]
        ).astype(np.float32)

        label_idx = 0
        score_label_map_text_label_list = []
        pos_list, pos_mask, label_list = [], [], []
        for poly_idx, poly_tag in enumerate(zip(polys, tags)):
            poly = poly_tag[0]
            tag = poly_tag[1]

            # generate min_area_quad
            min_area_quad, center_point = self.gen_min_area_quad_from_poly(poly)
            min_area_quad_h = 0.5 * (
                np.linalg.norm(min_area_quad[0] - min_area_quad[3])
                + np.linalg.norm(min_area_quad[1] - min_area_quad[2])
            )
            min_area_quad_w = 0.5 * (
                np.linalg.norm(min_area_quad[0] - min_area_quad[1])
                + np.linalg.norm(min_area_quad[2] - min_area_quad[3])
            )

            if (
                min(min_area_quad_h, min_area_quad_w) < self.min_text_size * ds_ratio
                or min(min_area_quad_h, min_area_quad_w) > self.max_text_size * ds_ratio
            ):
                continue

            if tag:
                cv2.fillPoly(
                    training_mask, poly.astype(np.int32)[np.newaxis, :, :], 0.15
                )
            else:
                text_label = text_strs[poly_idx]
                text_label = self.prepare_text_label(text_label, self.Lexicon_Table)
                text_label_index_list = [
                    [self.Lexicon_Table.index(c_)]
                    for c_ in text_label
                    if c_ in self.Lexicon_Table
                ]
                if len(text_label_index_list) < 1:
                    continue

                tcl_poly = self.poly2tcl(poly, tcl_ratio)
                tcl_quads = self.poly2quads(tcl_poly)
                poly_quads = self.poly2quads(poly)

                stcl_quads, quad_index = self.shrink_poly_along_width(
                    tcl_quads,
                    shrink_ratio_of_width=shrink_ratio_of_width,
                    expand_height_ratio=1.0 / tcl_ratio,
                )

                cv2.fillPoly(score_map, np.round(stcl_quads).astype(np.int32), 1.0)
                cv2.fillPoly(
                    score_map_big, np.round(stcl_quads / ds_ratio).astype(np.int32), 1.0
                )

                for idx, quad in enumerate(stcl_quads):
                    quad_mask = np.zeros((h, w), dtype=np.float32)
                    quad_mask = cv2.fillPoly(
                        quad_mask,
                        np.round(quad[np.newaxis, :, :]).astype(np.int32),
                        1.0,
                    )
                    tbo_map = self.gen_quad_tbo(
                        poly_quads[quad_index[idx]], quad_mask, tbo_map
                    )

                # score label map and score_label_map_text_label_list for refine
                if label_idx == 0:
                    text_pos_list_ = [
                        [len(self.Lexicon_Table)],
                    ]
                    score_label_map_text_label_list.append(text_pos_list_)

                label_idx += 1
                cv2.fillPoly(
                    score_label_map, np.round(poly_quads).astype(np.int32), label_idx
                )
                score_label_map_text_label_list.append(text_label_index_list)

                # direction info, fix-me
                n_char = len(text_label_index_list)
                direction_map = self.generate_direction_map(
                    poly_quads, n_char, direction_map
                )

                # pos info
                average_shrink_height = self.calculate_average_height(stcl_quads)

                if self.point_gather_mode == "align":
                    self.f_direction = direction_map[:, :, :-1].copy()
                    pos_res = self.fit_and_gather_tcl_points_v3(
                        min_area_quad,
                        stcl_quads,
                        max_h=h,
                        max_w=w,
                        fixed_point_num=64,
                        img_id=self.img_id,
                        reference_height=average_shrink_height,
                    )
                    if pos_res is None:
                        continue
                    pos_l, pos_m = pos_res[0], pos_res[1]

                else:
                    pos_l, pos_m = self.fit_and_gather_tcl_points_v2(
                        min_area_quad,
                        poly,
                        max_h=h,
                        max_w=w,
                        fixed_point_num=64,
                        img_id=self.img_id,
                        reference_height=average_shrink_height,
                    )

                label_l = text_label_index_list
                if len(text_label_index_list) < 2:
                    continue

                pos_list.append(pos_l)
                pos_mask.append(pos_m)
                label_list.append(label_l)

        # use big score_map for smooth tcl lines
        score_map_big_resized = cv2.resize(
            score_map_big, dsize=None, fx=ds_ratio, fy=ds_ratio
        )
        score_map = np.array(score_map_big_resized > 1e-3, dtype="float32")

        return (
            score_map,
            score_label_map,
            tbo_map,
            direction_map,
            training_mask,
            pos_list,
            pos_mask,
            label_list,
            score_label_map_text_label_list,
        )