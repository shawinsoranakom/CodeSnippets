def create_document(self, question: str, answer: str, ranked_papers: list = None):
        """写入聊天历史
        Args:
            question: str, 用户问题
            answer: str, AI回答
            ranked_papers: list, 排序后的论文列表
        """
        try:
            # 添加标题
            title_para = self.doc.add_paragraph(style='Title_Custom')
            title_run = title_para.add_run('GPT-Academic 对话记录')

            # 添加日期
            try:
                date_para = self.doc.add_paragraph()
                date_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                date_run = date_para.add_run(datetime.now().strftime('%Y年%m月%d日'))
                date_run.font.name = '仿宋'
                date_run._element.rPr.rFonts.set(qn('w:eastAsia'), '仿宋')
                date_run.font.size = Pt(16)
            except Exception as e:
                print(f"添加日期失败: {str(e)}")
                raise

            self.doc.add_paragraph()  # 添加空行

            # 添加问答对话
            try:
                q_para = self.doc.add_paragraph(style='Question_Style')
                q_para.add_run('问题：').bold = True
                q_para.add_run(str(question))

                a_para = self.doc.add_paragraph(style='Answer_Style')
                a_para.add_run('回答：').bold = True
                a_para.add_run(convert_markdown_to_word(str(answer)))
            except Exception as e:
                print(f"添加问答对话失败: {str(e)}")
                raise

            # 添加参考文献部分
            if ranked_papers:
                try:
                    ref_title = self.doc.add_paragraph(style='Reference_Title_Style')
                    ref_title.add_run("参考文献")

                    for idx, paper in enumerate(ranked_papers, 1):
                        try:
                            ref_para = self.doc.add_paragraph(style='Reference_Style')
                            ref_para.add_run(f'[{idx}] ').bold = True

                            # 添加作者
                            authors = ', '.join(paper.authors[:3])
                            if len(paper.authors) > 3:
                                authors += ' et al.'
                            ref_para.add_run(f'{authors}. ')

                            # 添加标题
                            title_run = ref_para.add_run(paper.title)
                            title_run.italic = True
                            if hasattr(paper, 'url') and paper.url:
                                try:
                                    title_run._element.rPr.rStyle = self._create_hyperlink_style()
                                    self._add_hyperlink(ref_para, paper.title, paper.url)
                                except Exception as e:
                                    print(f"添加超链接失败: {str(e)}")

                            # 添加期刊/会议信息
                            if paper.venue_name:
                                ref_para.add_run(f'. {paper.venue_name}')

                            # 添加年份
                            if paper.year:
                                ref_para.add_run(f', {paper.year}')

                            # 添加DOI
                            if paper.doi:
                                ref_para.add_run('. ')
                                if "arxiv" in paper.url:
                                    doi_url = paper.doi
                                else:
                                    doi_url = f'https://doi.org/{paper.doi}'
                                self._add_hyperlink(ref_para, f'DOI: {paper.doi}', doi_url)

                            ref_para.add_run('.')
                        except Exception as e:
                            print(f"添加第 {idx} 篇参考文献失败: {str(e)}")
                            continue
                except Exception as e:
                    print(f"添加参考文献部分失败: {str(e)}")
                    raise

            return self.doc

        except Exception as e:
            print(f"Word文档创建失败: {str(e)}")
            import traceback
            print(f"详细错误信息: {traceback.format_exc()}")
            raise