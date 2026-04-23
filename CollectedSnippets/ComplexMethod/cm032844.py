def __call__(self, filename, binary=None, from_page=0,
                 to_page=100000, zoomin=3, callback=None):
        from timeit import default_timer as timer
        start = timer()
        callback(msg="OCR started")
        self.__images__(
            filename if not binary else binary,
            zoomin,
            from_page,
            to_page,
            callback
        )
        callback(msg="OCR finished ({:.2f}s)".format(timer() - start))

        start = timer()
        self._layouts_rec(zoomin)
        callback(0.63, "Layout analysis ({:.2f}s)".format(timer() - start))
        logging.debug(f"layouts cost: {timer() - start}s")

        start = timer()
        self._table_transformer_job(zoomin)
        callback(0.68, "Table analysis ({:.2f}s)".format(timer() - start))

        start = timer()
        self._text_merge()
        tbls = self._extract_table_figure(True, zoomin, True, True)
        column_width = np.median([b["x1"] - b["x0"] for b in self.boxes])
        self._concat_downward()
        self._filter_forpages()
        callback(0.75, "Text merged ({:.2f}s)".format(timer() - start))

        # clean mess
        if column_width < self.page_images[0].size[0] / zoomin / 2:
            logging.debug("two_column................... {} {}".format(column_width,
                                                                       self.page_images[0].size[0] / zoomin / 2))
            self.boxes = self.sort_X_by_page(self.boxes, column_width / 2)
        for b in self.boxes:
            b["text"] = re.sub(r"([\t 　]|\u3000){2,}", " ", b["text"].strip())

        def _begin(txt):
            return re.match(
                "[0-9. 一、i]*(introduction|abstract|摘要|引言|keywords|key words|关键词|background|背景|目录|前言|contents)",
                txt.lower().strip())

        if from_page > 0:
            return {
                "title": "",
                "authors": "",
                "abstract": "",
                "sections": [(b["text"] + self._line_tag(b, zoomin), b.get("layoutno", "")) for b in self.boxes if
                             re.match(r"(text|title)", b.get("layoutno", "text"))],
                "tables": tbls
            }
        # get title and authors
        title = ""
        authors = []
        i = 0
        while i < min(32, len(self.boxes) - 1):
            b = self.boxes[i]
            i += 1
            if b.get("layoutno", "").find("title") >= 0:
                title = b["text"]
                if _begin(title):
                    title = ""
                    break
                for j in range(3):
                    next_idx = i + j
                    if next_idx >= len(self.boxes):
                        break
                    candidate = self.boxes[next_idx]["text"]
                    if _begin(candidate):
                        break
                    if "@" in candidate:
                        break
                    authors.append(candidate)
                break
        # get abstract
        abstr = ""
        i = 0
        while i + 1 < min(32, len(self.boxes)):
            b = self.boxes[i]
            i += 1
            txt = b["text"].lower().strip()
            if re.match("(abstract|摘要)", txt):
                if len(txt.split()) > 32 or len(txt) > 64:
                    abstr = txt + self._line_tag(b, zoomin)
                    break
                txt = self.boxes[i]["text"].lower().strip()
                if len(txt.split()) > 32 or len(txt) > 64:
                    abstr = txt + self._line_tag(self.boxes[i], zoomin)
                i += 1
                break
        if not abstr:
            i = 0

        callback(
            0.8, "Page {}~{}: Text merging finished".format(
                from_page, min(
                    to_page, self.total_page)))
        for b in self.boxes:
            logging.debug("{} {}".format(b["text"], b.get("layoutno")))
        logging.debug("{}".format(tbls))

        return {
            "title": title,
            "authors": " ".join(authors),
            "abstract": abstr,
            "sections": [(b["text"] + self._line_tag(b, zoomin), b.get("layoutno", "")) for b in self.boxes[i:] if
                         re.match(r"(text|title)", b.get("layoutno", "text"))],
            "tables": tbls
        }