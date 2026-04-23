def create_document(self, content: str, processing_type: str = "文本处理"):
        """创建文档，保留原始结构"""
        # 添加标题
        title_para = self.doc.add_paragraph(style='Title_Custom')
        title_run = title_para.add_run('文档处理结果')

        # 添加处理类型
        processing_para = self.doc.add_paragraph()
        processing_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        processing_run = processing_para.add_run(f"处理方式: {processing_type}")
        processing_run.font.name = '仿宋'
        processing_run._element.rPr.rFonts.set(qn('w:eastAsia'), '仿宋')
        processing_run.font.size = Pt(14)

        # 添加日期
        date_para = self.doc.add_paragraph()
        date_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        date_run = date_para.add_run(f"处理时间: {datetime.now().strftime('%Y年%m月%d日')}")
        date_run.font.name = '仿宋'
        date_run._element.rPr.rFonts.set(qn('w:eastAsia'), '仿宋')
        date_run.font.size = Pt(14)

        self.doc.add_paragraph()  # 添加空行

        # 预处理内容，将Markdown格式转换为适合Word的格式
        processed_content = convert_markdown_to_word(content)

        # 按行处理文本，保留结构
        lines = processed_content.split('\n')
        in_code_block = False
        current_paragraph = None

        for line in lines:
            # 检查是否为标题
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)

            if header_match:
                # 根据#的数量确定标题级别
                level = len(header_match.group(1))
                title_text = header_match.group(2)

                if level == 1:
                    style = 'Heading1_Custom'
                elif level == 2:
                    style = 'Heading2_Custom'
                else:
                    style = 'Heading3_Custom'

                self.doc.add_paragraph(title_text, style=style)
                current_paragraph = None

            # 检查代码块标记
            elif '[代码块]' in line:
                in_code_block = True
                current_paragraph = self.doc.add_paragraph(style='Code_Custom')
                code_line = line.replace('[代码块]', '').strip()
                if code_line:
                    current_paragraph.add_run(code_line)

            elif '[/代码块]' in line:
                in_code_block = False
                code_line = line.replace('[/代码块]', '').strip()
                if code_line and current_paragraph:
                    current_paragraph.add_run(code_line)
                current_paragraph = None

            # 检查列表项
            elif line.strip().startswith('•'):
                p = self.doc.add_paragraph(style='List_Custom')
                p.add_run(line.strip())
                current_paragraph = None

            # 处理普通文本行
            elif line.strip():
                if in_code_block:
                    if current_paragraph:
                        current_paragraph.add_run('\n' + line)
                    else:
                        current_paragraph = self.doc.add_paragraph(line, style='Code_Custom')
                else:
                    if current_paragraph is None or not current_paragraph.text:
                        current_paragraph = self.doc.add_paragraph(line, style='Normal_Custom')
                    else:
                        current_paragraph.add_run('\n' + line)

            # 处理空行，创建新段落
            elif not in_code_block:
                current_paragraph = None

        return self.doc