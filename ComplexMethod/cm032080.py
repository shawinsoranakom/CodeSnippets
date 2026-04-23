def _add_heading(self, text: str, level: int):
        """
        添加带编号的标题

        Args:
            text: 标题文本
            level: 标题级别 (0-3)
        """
        style_map = {
            0: 'Title_Custom',
            1: 'Heading1_Custom',
            2: 'Heading2_Custom',
            3: 'Heading3_Custom'
        }

        number = self._get_heading_number(level)
        paragraph = self.doc.add_paragraph(style=style_map[level])

        if number:
            number_run = paragraph.add_run(number)
            font_size = 22 if level == 1 else (18 if level == 2 else 16)
            self._get_run_style(number_run, '黑体', font_size, True)

        text_run = paragraph.add_run(text)
        font_size = 32 if level == 0 else (22 if level == 1 else (18 if level == 2 else 16))
        self._get_run_style(text_run, '黑体', font_size, True)

        # 主标题添加日期
        if level == 0:
            date_paragraph = self.doc.add_paragraph()
            date_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
            date_run = date_paragraph.add_run(datetime.now().strftime('%Y年%m月%d日'))
            self._get_run_style(date_run, '仿宋', 16, False)

        return paragraph