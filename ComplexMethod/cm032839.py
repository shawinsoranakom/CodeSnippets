def __call__(self, filename, binary=None, from_page=0,
                 to_page=100000, zoomin=3, callback=None):
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
        logging.debug("OCR({}~{}): {:.2f}s".format(from_page, to_page, timer() - start))
        start = timer()
        self._layouts_rec(zoomin, drop=False)
        callback(0.63, "Layout analysis ({:.2f}s)".format(timer() - start))

        start = timer()
        self._table_transformer_job(zoomin)
        callback(0.65, "Table analysis ({:.2f}s)".format(timer() - start))

        start = timer()
        self._text_merge()
        callback(0.67, "Text merged ({:.2f}s)".format(timer() - start))
        tbls = self._extract_table_figure(True, zoomin, True, True)
        # self._naive_vertical_merge()
        # self._concat_downward()
        # self._filter_forpages()
        logging.debug("layouts: {}".format(timer() - start))
        sections = [b["text"] for b in self.boxes]
        bull_x0_list = []
        q_bull, reg = qbullets_category(sections)
        if q_bull == -1:
            raise ValueError("Unable to recognize Q&A structure.")
        qai_list = []
        last_q, last_a, last_tag = '', '', ''
        last_index = -1
        last_box = {'text': ''}
        last_bull = None

        def sort_key(element):
            tbls_pn = element[1][0][0]
            tbls_top = element[1][0][3]
            return tbls_pn, tbls_top

        tbls.sort(key=sort_key)
        tbl_index = 0
        last_pn, last_bottom = 0, 0
        tbl_pn, tbl_left, tbl_right, tbl_top, tbl_bottom, tbl_tag, tbl_text = 1, 0, 0, 0, 0, '@@0\t0\t0\t0\t0##', ''
        for box in self.boxes:
            section, line_tag = box['text'], self._line_tag(box, zoomin)
            has_bull, index = has_qbullet(reg, box, last_box, last_index, last_bull, bull_x0_list)
            last_box, last_index, last_bull = box, index, has_bull
            line_pn = get_float(line_tag.lstrip('@@').split('\t')[0])
            line_top = get_float(line_tag.rstrip('##').split('\t')[3])
            tbl_pn, tbl_left, tbl_right, tbl_top, tbl_bottom, tbl_tag, tbl_text = self.get_tbls_info(tbls, tbl_index)
            if not has_bull:  # No question bullet
                if not last_q:
                    if tbl_pn < line_pn or (tbl_pn == line_pn and tbl_top <= line_top):  # image passed
                        tbl_index += 1
                    continue
                else:
                    sum_tag = line_tag
                    sum_section = section
                    while ((tbl_pn == last_pn and tbl_top >= last_bottom) or (tbl_pn > last_pn)) \
                            and ((tbl_pn == line_pn and tbl_top <= line_top) or (
                            tbl_pn < line_pn)):  # add image at the middle of current answer
                        sum_tag = f'{tbl_tag}{sum_tag}'
                        sum_section = f'{tbl_text}{sum_section}'
                        tbl_index += 1
                        tbl_pn, tbl_left, tbl_right, tbl_top, tbl_bottom, tbl_tag, tbl_text = self.get_tbls_info(tbls,
                                                                                                                 tbl_index)
                    last_a = f'{last_a}{sum_section}'
                    last_tag = f'{last_tag}{sum_tag}'
            else:
                if last_q:
                    while ((tbl_pn == last_pn and tbl_top >= last_bottom) or (tbl_pn > last_pn)) \
                            and ((tbl_pn == line_pn and tbl_top <= line_top) or (
                            tbl_pn < line_pn)):  # add image at the end of last answer
                        last_tag = f'{last_tag}{tbl_tag}'
                        last_a = f'{last_a}{tbl_text}'
                        tbl_index += 1
                        tbl_pn, tbl_left, tbl_right, tbl_top, tbl_bottom, tbl_tag, tbl_text = self.get_tbls_info(tbls,
                                                                                                                 tbl_index)
                    image, poss = self.crop(last_tag, need_position=True)
                    qai_list.append((last_q, last_a, image, poss))
                    last_q, last_a, last_tag = '', '', ''
                last_q = has_bull.group()
                _, end = has_bull.span()
                last_a = section[end:]
                last_tag = line_tag
            last_bottom = float(line_tag.rstrip('##').split('\t')[4])
            last_pn = line_pn
        if last_q:
            qai_list.append((last_q, last_a, *self.crop(last_tag, need_position=True)))
        return qai_list, tbls