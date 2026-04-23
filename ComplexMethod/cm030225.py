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