def __call__(self, filename, binary=None, from_page=0, to_page=100000, zoomin=3, callback=None, **kwargs):
        # 1. OCR
        callback(msg="OCR started")
        self.__images__(filename if not binary else binary, zoomin, from_page, to_page, callback)

        # 2. Layout Analysis
        callback(msg="Layout Analysis")
        self._layouts_rec(zoomin)

        # 3. Table Analysis
        callback(msg="Table Analysis")
        self._table_transformer_job(zoomin)

        # 4. Text Merge
        self._text_merge()

        # 5. Extract Tables (Force HTML)
        tbls = self._extract_table_figure(True, zoomin, True, True)

        # 6. Re-assemble Page Content
        page_items = defaultdict(list)

        # (A) Add text
        for b in self.boxes:
            # b["page_number"] is relative page number，must + from_page
            global_page_num = b["page_number"] + from_page
            if not (from_page < global_page_num <= to_page + from_page):
                continue
            page_items[global_page_num].append({"top": b["top"], "x0": b["x0"], "text": b["text"], "type": "text"})

        # (B) Add table and figure
        for (img, content), positions in tbls:
            if not positions:
                continue

            if isinstance(content, list):
                final_text = "\n".join(content)
            elif isinstance(content, str):
                final_text = content
            else:
                final_text = str(content)

            try:
                pn_index = positions[0][0]
                if isinstance(pn_index, list):
                    pn_index = pn_index[0]

                # pn_index in tbls is absolute page number
                current_page_num = int(pn_index) + 1
            except Exception as e:
                print(f"Error parsing position: {e}")
                continue

            if not (from_page < current_page_num <= to_page + from_page):
                continue

            top = positions[0][3]
            left = positions[0][1]

            page_items[current_page_num].append({"top": top, "x0": left, "text": final_text, "type": "table_or_figure"})

        # 7. Generate result
        res = []
        for i in range(len(self.page_images)):
            current_pn = from_page + i + 1
            items = page_items.get(current_pn, [])
            # Sort by vertical position
            items.sort(key=lambda x: (x["top"], x["x0"]))
            full_page_text = "\n\n".join([item["text"] for item in items])
            if not full_page_text.strip():
                full_page_text = f"[No text or data found in Page {current_pn}]"
            page_img = self.page_images[i]
            res.append((full_page_text, page_img))

        callback(0.9, "Parsing finished")

        return res, []