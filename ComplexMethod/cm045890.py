def _get_paragraph_elements(self, paragraph: Paragraph):
        """
        提取段落元素及其格式和超链接信息。

        Args:
            paragraph: 段落对象

        Returns:
            list[tuple[str, Optional[Formatting], Optional[Union[AnyUrl, Path, str]]]]:
            段落元素列表，每个元素包含文本、格式和超链接信息
        """

        inner_contents = list(self._iter_paragraph_inner_content(paragraph))
        paragraph_text = self._get_paragraph_text_from_contents(inner_contents)

        # 目前保留空段落以保持向后兼容性:
        if paragraph_text.strip() == "":
            # 检查是否存在带可见样式（下划线或删除线）的空白文本 run。
            # 有可见样式的空白文本（如带下划线的空格）在视觉上是可见的，应予保留，
            # 因此跳过提前返回，交由后续完整 run 处理流程处理。
            has_visible_style_run = any(
                isinstance(c, Run) and c.text and self._has_visible_style(self._get_format_from_run(c))
                for c in inner_contents
            )
            if not has_visible_style_run:
                return [("", None, None)]

        paragraph_elements: list[
            tuple[str, Optional[Formatting], Optional[Union[AnyUrl, Path, str]]]
        ] = []
        group_text = ""
        previous_format = None

        # 字段代码超链接内联检测状态（处理 w:fldChar + w:instrText 形式的超链接）
        _W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        _field_in = False       # 当前是否在字段域内
        _field_url = None       # 当前字段域解析出的 URL
        _field_phase = None     # 'instr' 或 'result'
        _field_acc_text = ""    # 累积的显示文本
        _field_acc_format = None  # 首个显示 run 的格式

        # 遍历段落的 runs 并按格式分组
        for c in inner_contents:
            if isinstance(c, Hyperlink):
                # 若地址为 URL（含 ://），直接保留字符串，避免 Path 将 // 规范化为 /
                address = c.address
                if address and "://" in address:
                    hyperlink = address
                else:
                    hyperlink = Path(address) if address else Path(".")
                # Hyperlink 内可能包含多个 run（且样式不同，如 TOC 项中的删除线/斜体）。
                # 按 run 粒度展开，避免只取首个 run 导致样式丢失。
                if c.runs and len(c.runs) > 0:
                    # 先落盘当前累积的普通文本分组
                    prev_has_visible = len(group_text.strip()) > 0 or (
                        group_text and self._has_visible_style(previous_format)
                    )
                    if prev_has_visible:
                        paragraph_elements.append((group_text, previous_format, None))
                    group_text = ""

                    for h_run in c.runs:
                        # Skip hidden runs in hyperlinks, especially TOC page-number fields.
                        if self._is_hidden_run(h_run):
                            continue
                        h_text = h_run.text or ""
                        h_format = self._get_format_from_run(h_run)
                        # 保留非空文本（含制表符）以及带可见样式的空白 run
                        if h_text != "" or self._has_visible_style(h_format):
                            paragraph_elements.append((h_text, h_format, hyperlink))
                    # 保持 previous_format 为最近的普通文本格式，不跨越超链接合并
                    continue
                else:
                    text = c.text
                    format = None
            elif isinstance(c, Run):
                # ---- 字段代码超链接内联检测 ----
                fld_char = c._element.find(f"{{{_W_NS}}}fldChar")
                if fld_char is not None:
                    fld_type = fld_char.get(f"{{{_W_NS}}}fldCharType")
                    if fld_type == "begin":
                        _field_in = True
                        _field_url = None
                        _field_phase = "instr"
                        _field_acc_text = ""
                        _field_acc_format = None
                        continue
                    elif fld_type == "separate":
                        _field_phase = "result"
                        continue
                    elif fld_type == "end":
                        if _field_url and _field_acc_text.strip():
                            # 将累积的字段代码超链接作为一个整体处理
                            text = _field_acc_text
                            hyperlink = _field_url
                            format = _field_acc_format
                        elif _field_acc_text.strip():
                            # 非超链接字段（如 SEQ 序号字段），将累积的显示文本作为普通文本处理
                            text = _field_acc_text
                            hyperlink = None
                            format = _field_acc_format
                        else:
                            _field_in = False
                            _field_url = None
                            _field_phase = None
                            _field_acc_text = ""
                            _field_acc_format = None
                            continue
                        _field_in = False
                        _field_url = None
                        _field_phase = None
                        _field_acc_text = ""
                        _field_acc_format = None
                        # 继续执行下方的 hyperlink 统一处理逻辑
                    else:
                        continue
                else:
                    instr_elem = c._element.find(f"{{{_W_NS}}}instrText")
                    if instr_elem is not None and _field_phase == "instr":
                        # 捕获 HYPERLINK 指令中的 URL
                        if instr_elem.text:
                            m = re.search(r'HYPERLINK\s+"([^"]+)"', instr_elem.text)
                            if m:
                                _field_url = m.group(1)
                        continue

                    if _field_in and _field_phase == "result":
                        # 显示文本 run：累积到字段文本
                        t_elem = c._element.find(f"{{{_W_NS}}}t")
                        if t_elem is not None:
                            _field_acc_text += c.text
                            if _field_acc_format is None:
                                _field_acc_format = self._get_format_from_run(c)
                        continue

                    # 普通 run
                    text = c.text
                    hyperlink = None
                    format = self._get_format_from_run(c)
            else:
                continue

            # 当新 run 有可见内容（非空或带可见样式的空白）且格式变化时触发分组
            has_visible_content = len(text.strip()) > 0 or self._has_visible_style(format)
            if (has_visible_content and format != previous_format) or (
                hyperlink is not None
            ):
                # 前一组有实质内容（非空或带可见样式的空白）时才保存
                prev_has_visible = len(group_text.strip()) > 0 or (
                    group_text and self._has_visible_style(previous_format)
                )
                if prev_has_visible:
                    paragraph_elements.append(
                        (group_text, previous_format, None)
                    )
                group_text = ""

                # 如果有超链接，则立即添加
                if hyperlink is not None:
                    paragraph_elements.append((text.strip(), format, hyperlink))
                    text = ""
                else:
                    previous_format = format

            group_text += text

        # 格式化最后一个组
        # 注意：使用 previous_format（当前累积组的格式），而非 format（最后一次循环迭代的格式）。
        # 最后一次迭代可能是无样式的空 run，若使用 format 会导致样式丢失。
        last_has_visible = len(group_text.strip()) > 0 or (
            group_text and self._has_visible_style(previous_format)
        )
        if last_has_visible:
            paragraph_elements.append((group_text, previous_format, None))

        return paragraph_elements