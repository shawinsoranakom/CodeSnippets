def _extract_table_figure(self, need_image, ZM, return_html, need_position, separate_tables_figures=False):
        tables = {}
        figures = {}
        # extract figure and table boxes
        i = 0
        lst_lout_no = ""
        nomerge_lout_no = []
        while i < len(self.boxes):
            if "layoutno" not in self.boxes[i]:
                i += 1
                continue
            lout_no = str(self.boxes[i]["page_number"]) + "-" + str(self.boxes[i]["layoutno"])
            if TableStructureRecognizer.is_caption(self.boxes[i]) or self.boxes[i]["layout_type"] in ["table caption", "title", "figure caption", "reference"]:
                nomerge_lout_no.append(lst_lout_no)
            if self.boxes[i]["layout_type"] == "table":
                if re.match(r"(数据|资料|图表)*来源[:： ]", self.boxes[i]["text"]):
                    self.boxes.pop(i)
                    continue
                if lout_no not in tables:
                    tables[lout_no] = []
                tables[lout_no].append(self.boxes[i])
                self.boxes.pop(i)
                lst_lout_no = lout_no
                continue
            if need_image and self.boxes[i]["layout_type"] == "figure":
                if re.match(r"(数据|资料|图表)*来源[:： ]", self.boxes[i]["text"]):
                    self.boxes.pop(i)
                    continue
                if lout_no not in figures:
                    figures[lout_no] = []
                figures[lout_no].append(self.boxes[i])
                self.boxes.pop(i)
                lst_lout_no = lout_no
                continue
            i += 1

        # merge table on different pages
        nomerge_lout_no = set(nomerge_lout_no)
        tbls = sorted([(k, bxs) for k, bxs in tables.items()], key=lambda x: (x[1][0]["top"], x[1][0]["x0"]))

        i = len(tbls) - 1
        while i - 1 >= 0:
            k0, bxs0 = tbls[i - 1]
            k, bxs = tbls[i]
            i -= 1
            if k0 in nomerge_lout_no:
                continue
            if bxs[0]["page_number"] == bxs0[0]["page_number"]:
                continue
            if bxs[0]["page_number"] - bxs0[0]["page_number"] > 1:
                continue
            mh = self.mean_height[bxs[0]["page_number"] - 1]
            if self._y_dis(bxs0[-1], bxs[0]) > mh * 23:
                continue
            tables[k0].extend(tables[k])
            del tables[k]

        def x_overlapped(a, b):
            return not any([a["x1"] < b["x0"], a["x0"] > b["x1"]])

        # find captions and pop out
        i = 0
        while i < len(self.boxes):
            c = self.boxes[i]
            # mh = self.mean_height[c["page_number"]-1]
            if not TableStructureRecognizer.is_caption(c):
                i += 1
                continue

            # find the nearest layouts
            def nearest(tbls):
                nonlocal c
                mink = ""
                minv = 1000000000
                for k, bxs in tbls.items():
                    for b in bxs:
                        if b.get("layout_type", "").find("caption") >= 0:
                            continue
                        y_dis = self._y_dis(c, b)
                        x_dis = self._x_dis(c, b) if not x_overlapped(c, b) else 0
                        dis = y_dis * y_dis + x_dis * x_dis
                        if dis < minv:
                            mink = k
                            minv = dis
                return mink, minv

            tk, tv = nearest(tables)
            fk, fv = nearest(figures)
            # if min(tv, fv) > 2000:
            #    i += 1
            #    continue
            if tv < fv and tk:
                tables[tk].insert(0, c)
                logging.debug("TABLE:" + self.boxes[i]["text"] + "; Cap: " + tk)
            elif fk:
                figures[fk].insert(0, c)
                logging.debug("FIGURE:" + self.boxes[i]["text"] + "; Cap: " + tk)
            self.boxes.pop(i)

        def cropout(bxs, ltype, poss):
            nonlocal ZM
            max_page_index = len(self.page_images) - 1

            def local_page_index(page_number):
                idx = page_number - 1 if page_number > 0 else 0
                if idx > max_page_index and self.page_from:
                    idx = page_number - 1 - self.page_from
                return idx

            pn = set()
            for b in bxs:
                idx = local_page_index(b["page_number"])
                if 0 <= idx <= max_page_index:
                    pn.add(idx)
                else:
                    logging.warning(
                        "Skip out-of-range page_number %s (page_from=%s, pages=%s)",
                        b.get("page_number"),
                        self.page_from,
                        len(self.page_images),
                    )

            if not pn:
                return None

            if len(pn) < 2:
                pn = list(pn)[0]
                ht = self.page_cum_height[pn]
                b = {"x0": np.min([b["x0"] for b in bxs]), "top": np.min([b["top"] for b in bxs]) - ht, "x1": np.max([b["x1"] for b in bxs]), "bottom": np.max([b["bottom"] for b in bxs]) - ht}
                louts = [layout for layout in self.page_layout[pn] if layout["type"] == ltype]
                ii = Recognizer.find_overlapped(b, louts, naive=True)
                if ii is not None:
                    b = louts[ii]
                else:
                    logging.warning(f"Missing layout match: {pn + 1},%s" % (bxs[0].get("layoutno", "")))

                left, top, right, bott = b["x0"], b["top"], b["x1"], b["bottom"]
                if right < left:
                    right = left + 1
                poss.append((pn + self.page_from, left, right, top, bott))
                return self.page_images[pn].crop((left * ZM, top * ZM, right * ZM, bott * ZM))
            pn = {}
            for b in bxs:
                p = local_page_index(b["page_number"])
                if 0 <= p <= max_page_index:
                    if p not in pn:
                        pn[p] = []
                    pn[p].append(b)
            pn = sorted(pn.items(), key=lambda x: x[0])
            imgs = [cropout(arr, ltype, poss) for p, arr in pn]
            imgs = [img for img in imgs if img is not None]
            if not imgs:
                return None
            pic = Image.new("RGB", (int(np.max([i.size[0] for i in imgs])), int(np.sum([m.size[1] for m in imgs]))), (245, 245, 245))
            height = 0
            for img in imgs:
                pic.paste(img, (0, int(height)))
                height += img.size[1]
            return pic

        res = []
        positions = []
        figure_results = []
        figure_positions = []
        # crop figure out and add caption
        for k, bxs in figures.items():
            txt = "\n".join([b["text"] for b in bxs])
            if not txt:
                continue

            poss = []

            if separate_tables_figures:
                img = cropout(bxs, "figure", poss)
                if img is None:
                    continue
                figure_results.append((img, [txt]))
                figure_positions.append(poss)
            else:
                img = cropout(bxs, "figure", poss)
                if img is None:
                    continue
                res.append((img, [txt]))
                positions.append(poss)

        for k, bxs in tables.items():
            if not bxs:
                continue
            bxs = Recognizer.sort_Y_firstly(bxs, np.mean([(b["bottom"] - b["top"]) / 2 for b in bxs]))

            poss = []

            img = cropout(bxs, "table", poss)
            if img is None:
                continue
            res.append((img, self.tbl_det.construct_table(bxs, html=return_html, is_english=self.is_english)))
            positions.append(poss)

        if separate_tables_figures:
            assert len(positions) + len(figure_positions) == len(res) + len(figure_results)
            if need_position:
                return list(zip(res, positions)), list(zip(figure_results, figure_positions))
            else:
                return res, figure_results
        else:
            assert len(positions) == len(res)
            if need_position:
                return list(zip(res, positions))
            else:
                return res