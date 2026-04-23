def format_frame_summary(self, frame_summary, **kwargs):
        """Format the lines for a single FrameSummary.

        Returns a string representing one frame involved in the stack. This
        gets called for every frame to be printed in the stack summary.
        """
        colorize = kwargs.get("colorize", False)
        row = []
        filename = frame_summary.filename
        if frame_summary.filename.startswith("<stdin-") and frame_summary.filename.endswith('>'):
            filename = "<stdin>"
        if colorize:
            theme = _colorize.get_theme(force_color=True).traceback
        else:
            theme = _colorize.get_theme(force_no_color=True).traceback
        row.append(
            '  File {}"{}"{}, line {}{}{}, in {}{}{}\n'.format(
                theme.filename,
                filename,
                theme.reset,
                theme.line_no,
                frame_summary.lineno,
                theme.reset,
                theme.frame,
                frame_summary.name,
                theme.reset,
            )
        )
        if frame_summary._dedented_lines and frame_summary._dedented_lines.strip():
            if (
                frame_summary.colno is None or
                frame_summary.end_colno is None
            ):
                # only output first line if column information is missing
                row.append(textwrap.indent(frame_summary.line, '    ') + "\n")
            else:
                # get first and last line
                all_lines_original = frame_summary._original_lines.splitlines()
                first_line = all_lines_original[0]
                # assume all_lines_original has enough lines (since we constructed it)
                last_line = all_lines_original[frame_summary.end_lineno - frame_summary.lineno]

                # character index of the start/end of the instruction
                start_offset = _byte_offset_to_character_offset(first_line, frame_summary.colno)
                end_offset = _byte_offset_to_character_offset(last_line, frame_summary.end_colno)

                all_lines = frame_summary._dedented_lines.splitlines()[
                    :frame_summary.end_lineno - frame_summary.lineno + 1
                ]

                # adjust start/end offset based on dedent
                dedent_characters = len(first_line) - len(all_lines[0])
                start_offset = max(0, start_offset - dedent_characters)
                end_offset = max(0, end_offset - dedent_characters)

                # When showing this on a terminal, some of the non-ASCII characters
                # might be rendered as double-width characters, so we need to take
                # that into account when calculating the length of the line.
                dp_start_offset = _display_width(all_lines[0], offset=start_offset)
                dp_end_offset = _display_width(all_lines[-1], offset=end_offset)

                # get exact code segment corresponding to the instruction
                segment = "\n".join(all_lines)
                segment = segment[start_offset:len(segment) - (len(all_lines[-1]) - end_offset)]

                # attempt to parse for anchors
                anchors = None
                show_carets = False
                with suppress(Exception):
                    anchors = _extract_caret_anchors_from_line_segment(segment)
                show_carets = self._should_show_carets(start_offset, end_offset, all_lines, anchors)

                result = []

                # only display first line, last line, and lines around anchor start/end
                significant_lines = {0, len(all_lines) - 1}

                anchors_left_end_offset = 0
                anchors_right_start_offset = 0
                primary_char = "^"
                secondary_char = "^"
                if anchors:
                    anchors_left_end_offset = anchors.left_end_offset
                    anchors_right_start_offset = anchors.right_start_offset
                    # computed anchor positions do not take start_offset into account,
                    # so account for it here
                    if anchors.left_end_lineno == 0:
                        anchors_left_end_offset += start_offset
                    if anchors.right_start_lineno == 0:
                        anchors_right_start_offset += start_offset

                    # account for display width
                    anchors_left_end_offset = _display_width(
                        all_lines[anchors.left_end_lineno], offset=anchors_left_end_offset
                    )
                    anchors_right_start_offset = _display_width(
                        all_lines[anchors.right_start_lineno], offset=anchors_right_start_offset
                    )

                    primary_char = anchors.primary_char
                    secondary_char = anchors.secondary_char
                    significant_lines.update(
                        range(anchors.left_end_lineno - 1, anchors.left_end_lineno + 2)
                    )
                    significant_lines.update(
                        range(anchors.right_start_lineno - 1, anchors.right_start_lineno + 2)
                    )

                # remove bad line numbers
                significant_lines.discard(-1)
                significant_lines.discard(len(all_lines))

                def output_line(lineno):
                    """output all_lines[lineno] along with carets"""
                    result.append(all_lines[lineno] + "\n")
                    if not show_carets:
                        return
                    num_spaces = len(all_lines[lineno]) - len(all_lines[lineno].lstrip())
                    carets = []
                    num_carets = dp_end_offset if lineno == len(all_lines) - 1 else _display_width(all_lines[lineno])
                    # compute caret character for each position
                    for col in range(num_carets):
                        if col < num_spaces or (lineno == 0 and col < dp_start_offset):
                            # before first non-ws char of the line, or before start of instruction
                            carets.append(' ')
                        elif anchors and (
                            lineno > anchors.left_end_lineno or
                            (lineno == anchors.left_end_lineno and col >= anchors_left_end_offset)
                        ) and (
                            lineno < anchors.right_start_lineno or
                            (lineno == anchors.right_start_lineno and col < anchors_right_start_offset)
                        ):
                            # within anchors
                            carets.append(secondary_char)
                        else:
                            carets.append(primary_char)
                    if colorize:
                        # Replace the previous line with a red version of it only in the parts covered
                        # by the carets.
                        line = result[-1]
                        colorized_line_parts = []
                        colorized_carets_parts = []

                        for color, group in itertools.groupby(_zip_display_width(line, carets), key=lambda x: x[1]):
                            caret_group = list(group)
                            if "^" in color:
                                colorized_line_parts.append(theme.error_highlight + "".join(char for char, _ in caret_group) + theme.reset)
                                colorized_carets_parts.append(theme.error_highlight + "".join(caret for _, caret in caret_group) + theme.reset)
                            elif "~" in color:
                                colorized_line_parts.append(theme.error_range + "".join(char for char, _ in caret_group) + theme.reset)
                                colorized_carets_parts.append(theme.error_range + "".join(caret for _, caret in caret_group) + theme.reset)
                            else:
                                colorized_line_parts.append("".join(char for char, _ in caret_group))
                                colorized_carets_parts.append("".join(caret for _, caret in caret_group))

                        colorized_line = "".join(colorized_line_parts)
                        colorized_carets = "".join(colorized_carets_parts)
                        result[-1] = colorized_line
                        result.append(colorized_carets + "\n")
                    else:
                        result.append("".join(carets) + "\n")

                # display significant lines
                sig_lines_list = sorted(significant_lines)
                for i, lineno in enumerate(sig_lines_list):
                    if i:
                        linediff = lineno - sig_lines_list[i - 1]
                        if linediff == 2:
                            # 1 line in between - just output it
                            output_line(lineno - 1)
                        elif linediff > 2:
                            # > 1 line in between - abbreviate
                            result.append(f"...<{linediff - 1} lines>...\n")
                    output_line(lineno)

                row.append(
                    textwrap.indent(textwrap.dedent("".join(result)), '    ', lambda line: True)
                )
        if frame_summary.locals:
            for name, value in sorted(frame_summary.locals.items()):
                row.append('    {name} = {value}\n'.format(name=name, value=value))

        return ''.join(row)