def _table_transformer_job(self, ZM, auto_rotate=True):
        """
        Process table structure recognition.

        When auto_rotate=True, the complete workflow:
        1. Evaluate table orientation and select the best rotation angle
        2. Use rotated image for table structure recognition (TSR)
        3. Re-OCR the rotated image
        4. Match new OCR results with TSR cell coordinates

        Args:
            ZM: Zoom factor
            auto_rotate: Whether to enable auto orientation correction
        """
        logging.debug("Table processing...")
        imgs, pos = [], []
        tbcnt = [0]
        MARGIN = 10
        self.tb_cpns = []
        self.table_rotations = {}  # Store rotation info for each table
        self.rotated_table_imgs = {}  # Store rotated table images

        assert len(self.page_layout) == len(self.page_images)

        # Collect layout info for all tables
        table_layouts = []  # [(page, table_layout, left, top, right, bott), ...]

        table_index = 0
        for p, tbls in enumerate(self.page_layout):  # for page
            tbls = [f for f in tbls if f["type"] == "table"]
            tbcnt.append(len(tbls))
            if not tbls:
                continue
            for tb in tbls:  # for table
                left, top, right, bott = tb["x0"] - MARGIN, tb["top"] - MARGIN, tb["x1"] + MARGIN, tb["bottom"] + MARGIN
                left *= ZM
                top *= ZM
                right *= ZM
                bott *= ZM
                pos.append((left, top, p, table_index))  # Add page and table_index

                # Record table layout info
                table_layouts.append({"page": p, "table_index": table_index, "layout": tb, "coords": (left, top, right, bott)})

                # Crop table image
                table_img = self.page_images[p].crop((left, top, right, bott))

                if auto_rotate:
                    # Evaluate table orientation
                    logging.debug(f"Evaluating orientation for table {table_index} on page {p}")
                    best_angle, rotated_img, rotation_scores = self._evaluate_table_orientation(table_img)

                    # Store rotation info
                    self.table_rotations[table_index] = {
                        "page": p,
                        "original_pos": (left, top, right, bott),
                        "best_angle": best_angle,
                        "scores": rotation_scores,
                        "rotated_size": rotated_img.size,  # (width, height)
                    }

                    # Store the rotated image
                    self.rotated_table_imgs[table_index] = rotated_img
                    imgs.append(rotated_img)

                else:
                    imgs.append(table_img)
                    self.table_rotations[table_index] = {"page": p, "original_pos": (left, top, right, bott), "best_angle": 0, "scores": {}, "rotated_size": table_img.size}
                    self.rotated_table_imgs[table_index] = table_img

                table_index += 1

        assert len(self.page_images) == len(tbcnt) - 1
        if not imgs:
            return

        # Perform table structure recognition (TSR)
        recos = self.tbl_det(imgs)

        # If tables were rotated, re-OCR the rotated images and replace table boxes
        if auto_rotate:
            self._ocr_rotated_tables(ZM, table_layouts, recos, tbcnt)

        # Process TSR results (keep original logic but handle rotated coordinates)
        tbcnt = np.cumsum(tbcnt)
        for i in range(len(tbcnt) - 1):  # for page
            pg = []
            for j, tb_items in enumerate(recos[tbcnt[i] : tbcnt[i + 1]]):  # for table
                poss = pos[tbcnt[i] : tbcnt[i + 1]]
                for it in tb_items:  # for table components
                    # TSR coordinates are relative to rotated image, need to record
                    it["x0_rotated"] = it["x0"]
                    it["x1_rotated"] = it["x1"]
                    it["top_rotated"] = it["top"]
                    it["bottom_rotated"] = it["bottom"]

                    # For rotated tables, coordinate transformation to page space requires rotation
                    # Since we already re-OCR'd on rotated image, keep simple processing here
                    it["pn"] = poss[j][2]  # page number
                    it["layoutno"] = j
                    it["table_index"] = poss[j][3]  # table index
                    pg.append(it)
            self.tb_cpns.extend(pg)

        def gather(kwd, fzy=10, ption=0.6):
            eles = Recognizer.sort_Y_firstly([r for r in self.tb_cpns if re.match(kwd, r["label"])], fzy)
            eles = Recognizer.layouts_cleanup(self.boxes, eles, 5, ption)
            return Recognizer.sort_Y_firstly(eles, 0)

        # add R,H,C,SP tag to boxes within table layout
        headers = gather(r".*header$")
        rows = gather(r".* (row|header)")
        spans = gather(r".*spanning")
        clmns = sorted([r for r in self.tb_cpns if re.match(r"table column$", r["label"])], key=lambda x: (x["pn"], x["layoutno"], x["x0_rotated"] if "x0_rotated" in x else x["x0"]))
        clmns = Recognizer.layouts_cleanup(self.boxes, clmns, 5, 0.5)

        for b in self.boxes:
            if b.get("layout_type", "") != "table":
                continue
            ii = Recognizer.find_overlapped_with_threshold(b, rows, thr=0.3)
            if ii is not None:
                b["R"] = ii
                b["R_top"] = rows[ii]["top"]
                b["R_bott"] = rows[ii]["bottom"]

            ii = Recognizer.find_overlapped_with_threshold(b, headers, thr=0.3)
            if ii is not None:
                b["H_top"] = headers[ii]["top"]
                b["H_bott"] = headers[ii]["bottom"]
                b["H_left"] = headers[ii]["x0"]
                b["H_right"] = headers[ii]["x1"]
                b["H"] = ii

            ii = Recognizer.find_horizontally_tightest_fit(b, clmns)
            if ii is not None:
                b["C"] = ii
                b["C_left"] = clmns[ii]["x0"]
                b["C_right"] = clmns[ii]["x1"]

            ii = Recognizer.find_overlapped_with_threshold(b, spans, thr=0.3)
            if ii is not None:
                b["H_top"] = spans[ii]["top"]
                b["H_bott"] = spans[ii]["bottom"]
                b["H_left"] = spans[ii]["x0"]
                b["H_right"] = spans[ii]["x1"]
                b["SP"] = ii