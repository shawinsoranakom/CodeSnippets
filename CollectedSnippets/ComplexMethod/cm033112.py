def __ocr(self, pagenum, img, chars, ZM=3, device_id: int | None = None):
        start = timer()
        bxs = self.ocr.detect(np.array(img), device_id)
        logging.info(f"__ocr detecting boxes of an image cost ({timer() - start}s)")

        start = timer()
        if not bxs:
            self.boxes.append([])
            return
        bxs = [(line[0], line[1][0]) for line in bxs]
        bxs = Recognizer.sort_Y_firstly(
            [
                {"x0": b[0][0] / ZM, "x1": b[1][0] / ZM, "top": b[0][1] / ZM, "text": "", "txt": t, "bottom": b[-1][1] / ZM, "chars": [], "page_number": pagenum}
                for b, t in bxs
                if b[0][0] <= b[1][0] and b[0][1] <= b[-1][1]
            ],
            self.mean_height[pagenum - 1] / 3,
        )

        # merge chars in the same rect
        for c in chars:
            ii = Recognizer.find_overlapped(c, bxs)
            if ii is None:
                self.lefted_chars.append(c)
                continue
            ch = c["bottom"] - c["top"]
            bh = bxs[ii]["bottom"] - bxs[ii]["top"]
            if abs(ch - bh) / max(ch, bh) >= 0.7 and c["text"] != " ":
                self.lefted_chars.append(c)
                continue
            bxs[ii]["chars"].append(c)

        for b in bxs:
            if not b["chars"]:
                del b["chars"]
                continue
            box_chars = b["chars"]
            m_ht = np.mean([c["height"] for c in box_chars])
            garbled_count = 0
            total_count = 0
            for c in Recognizer.sort_Y_firstly(box_chars, m_ht):
                if c["text"] == " " and b["text"]:
                    if re.match(r"[0-9a-zA-Zа-яА-Я,.?;:!%%]", b["text"][-1]):
                        b["text"] += " "
                else:
                    b["text"] += c["text"]
                    for ch in c["text"]:
                        if not ch.isspace():
                            total_count += 1
                            if self._is_garbled_char(ch):
                                garbled_count += 1
            del b["chars"]
            # If the majority of characters from pdfplumber are garbled,
            # clear the text so OCR recognition will be used as fallback.
            # Strategy 1: PUA / unmapped CID characters
            if total_count > 0 and garbled_count / total_count >= 0.5:
                logging.info(
                    "Page %d: detected garbled pdfplumber text (garbled=%d/%d), falling back to OCR for box at (%.1f, %.1f)",
                    pagenum, garbled_count, total_count, b["x0"], b["top"],
                )
                b["text"] = ""
                continue
            # Strategy 2: font-encoding garbling — all chars are ASCII
            # punctuation from subset fonts (no CJK output)
            if total_count > 0 and self._is_garbled_by_font_encoding(box_chars, min_chars=5):
                logging.info(
                    "Page %d: detected font-encoding garbled text (%d chars), falling back to OCR for box at (%.1f, %.1f)",
                    pagenum, total_count, b["x0"], b["top"],
                )
                b["text"] = ""

        logging.info(f"__ocr sorting {len(chars)} chars cost {timer() - start}s")
        start = timer()
        boxes_to_reg = []
        img_np = np.array(img)
        for b in bxs:
            if not b["text"]:
                left, right, top, bott = b["x0"] * ZM, b["x1"] * ZM, b["top"] * ZM, b["bottom"] * ZM
                b["box_image"] = self.ocr.get_rotate_crop_image(img_np, np.array([[left, top], [right, top], [right, bott], [left, bott]], dtype=np.float32))
                boxes_to_reg.append(b)
            del b["txt"]
        texts = self.ocr.recognize_batch([b["box_image"] for b in boxes_to_reg], device_id)
        for i in range(len(boxes_to_reg)):
            boxes_to_reg[i]["text"] = texts[i]
            del boxes_to_reg[i]["box_image"]
        logging.info(f"__ocr recognize {len(bxs)} boxes cost {timer() - start}s")
        bxs = [b for b in bxs if b["text"]]
        if self.mean_height[pagenum - 1] == 0:
            self.mean_height[pagenum - 1] = np.median([b["bottom"] - b["top"] for b in bxs])
        self.boxes.append(bxs)