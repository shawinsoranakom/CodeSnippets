def _extract_references(self, elements) -> List[Reference]:
        """提取文档中的参考文献"""
        references = []

        # 首先找到参考文献部分
        ref_section_start = -1
        for i, element in enumerate(elements):
            if isinstance(element, Title) and re.search(self.PAPER_SECTION_PATTERNS['references'], str(element), re.IGNORECASE):
                ref_section_start = i
                break

        if ref_section_start == -1:
            # 没有找到明确的参考文献部分，尝试在文档末尾寻找
            # 参考文献通常在文档的最后20%
            start_pos = int(len(elements) * 0.8)
            for i in range(start_pos, len(elements)):
                element_text = str(elements[i]).strip()
                # 常见的参考文献格式特征
                if re.match(r'^\[\d+\]|\(\d+\)|^\d+\.\s+[A-Z]', element_text):
                    ref_section_start = i
                    break

        if ref_section_start != -1:
            # 提取参考文献列表
            current_ref = None
            inside_ref = False  # 标记是否在一个参考文献项内

            for i in range(ref_section_start + 1, len(elements)):
                element = elements[i]

                # 忽略标题元素 - 这些可能是错误识别的参考文献部分
                if isinstance(element, Title):
                    # 检查是否是真正的参考文献部分结束标题
                    title_text = str(element).lower().strip()
                    if re.search(r'^(appendix|appendices|supplementary|acknowledgements?|附录|致谢)$', title_text):
                        # 遇到下一个主要章节，结束参考文献提取
                        break

                    # 对于可能是参考文献一部分的标题，将其内容合并到当前参考文献
                    if current_ref and inside_ref:
                        current_ref.text += " " + str(element)
                        continue

                element_text = str(element).strip()
                if not element_text:
                    continue

                # 检查是否是新的参考文献条目
                ref_start_match = re.match(r'^\[(\d+)\]|\((\d+)\)|^(\d+)\.\s+', element_text)

                if ref_start_match:
                    # 如果已有参考文献，保存它
                    if current_ref and current_ref.text:
                        references.append(current_ref)
                        inside_ref = False

                    # 提取引用ID
                    ref_id = ""
                    if ref_start_match.group(1):  # [1] 格式
                        ref_id = f"[{ref_start_match.group(1)}]"
                        # 移除ID前缀
                        element_text = re.sub(r'^\[\d+\]\s*', '', element_text)
                    elif ref_start_match.group(2):  # (1) 格式
                        ref_id = f"({ref_start_match.group(2)})"
                        # 移除ID前缀
                        element_text = re.sub(r'^\(\d+\)\s*', '', element_text)
                    elif ref_start_match.group(3):  # 1. 格式
                        ref_id = f"{ref_start_match.group(3)}."
                        # 移除ID前缀
                        element_text = re.sub(r'^\d+\.\s+', '', element_text)

                    # 创建新的参考文献
                    current_ref = Reference(id=ref_id, text=element_text)
                    inside_ref = True

                    # 尝试提取作者和年份
                    author_year_match = re.match(r'^([^,]+),\s*(?:\()?(\d{4})(?:\))?', element_text)
                    if author_year_match:
                        authors_text = author_year_match.group(1).strip()
                        # 尝试分割多个作者
                        authors = [a.strip() for a in re.split(r',|and|&|；|、|等', authors_text) if a.strip()]
                        current_ref.authors = authors
                        current_ref.year = author_year_match.group(2)

                elif current_ref and inside_ref:
                    # 继续当前参考文献
                    current_ref.text += " " + element_text

            # 添加最后一个参考文献
            if current_ref and current_ref.text:
                references.append(current_ref)

        return references