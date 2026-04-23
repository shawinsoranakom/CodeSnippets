def insert_table_figures(tbls_or_figs, layout_type):
            def min_rectangle_distance(rect1, rect2):
                pn1, left1, right1, top1, bottom1 = rect1
                pn2, left2, right2, top2, bottom2 = rect2
                if right1 >= left2 and right2 >= left1 and bottom1 >= top2 and bottom2 >= top1:
                    return 0
                if right1 < left2:
                    dx = left2 - right1
                elif right2 < left1:
                    dx = left1 - right2
                else:
                    dx = 0
                if bottom1 < top2:
                    dy = top2 - bottom1
                elif bottom2 < top1:
                    dy = top1 - bottom2
                else:
                    dy = 0
                return math.sqrt(dx * dx + dy * dy)  # + (pn2-pn1)*10000

            for (img, txt), poss in tbls_or_figs:
                # Positions coming from _extract_table_figure carry absolute 0-based page
                # indices (page_from offset). Convert back to chunk-local indices so we
                # stay consistent with self.boxes/page_cum_height, which are all relative
                # to the current parsing window.
                local_poss = []
                for pn, left, right, top, bott in poss:
                    local_pn = pn - self.page_from
                    if 0 <= local_pn < len(self.page_cum_height) - 1:
                        local_poss.append((local_pn, left, right, top, bott))
                    else:
                        logging.debug(f"Skip out-of-range table/figure position pn={pn}, page_from={self.page_from}")
                if not local_poss:
                    logging.debug("No valid local positions for table/figure; skip insertion.")
                    continue

                if isinstance(txt, list):
                    txt = "\n".join(txt)
                pn, left, right, top, bott = local_poss[0]
                insert_at = len(self.boxes)
                bboxes = [(i, (b["page_number"], b["x0"], b["x1"], b["top"], b["bottom"])) for i, b in enumerate(self.boxes)]
                if bboxes:
                    dists = [
                        (min_rectangle_distance((cand_pn, cand_left, cand_right, cand_top + self.page_cum_height[cand_pn], cand_bott + self.page_cum_height[cand_pn]), rect), i)
                        for i, rect in bboxes
                        for cand_pn, cand_left, cand_right, cand_top, cand_bott in local_poss
                    ]
                    if dists:
                        nearest_bbox_idx = int(np.argmin([dist for dist, _ in dists]))
                        insert_at, _ = bboxes[dists[nearest_bbox_idx][-1]]
                        if self.boxes[insert_at]["bottom"] < top + self.page_cum_height[pn]:
                            insert_at += 1
                else:
                    logging.debug("No text boxes available; append %s block directly.", layout_type)
                self.boxes.insert(
                    insert_at,
                    {
                        "page_number": pn + 1,
                        "x0": left,
                        "x1": right,
                        "top": top + self.page_cum_height[pn],
                        "bottom": bott + self.page_cum_height[pn],
                        "layout_type": layout_type,
                        "text": txt,
                        "image": img,
                        "positions": [[pn + 1, int(left), int(right), int(top), int(bott)]],
                    },
                )