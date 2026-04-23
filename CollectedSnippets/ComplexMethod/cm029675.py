def _format_usage(self, usage, actions, groups, prefix):
        t = self._theme

        if prefix is None:
            prefix = _('usage: ')

        # if usage is specified, use that
        if usage is not None:
            usage = (
                t.prog_extra
                + usage
                % {"prog": f"{t.prog}{self._prog}{t.reset}{t.prog_extra}"}
                + t.reset
            )

        # if no optionals or positionals are available, usage is just prog
        elif usage is None and not actions:
            usage = f"{t.prog}{self._prog}{t.reset}"

        # if optionals and positionals are available, calculate usage
        elif usage is None:
            prog = '%(prog)s' % dict(prog=self._prog)

            parts, pos_start = self._get_actions_usage_parts(actions, groups)
            # build full usage string
            usage = ' '.join(filter(None, [prog, *parts]))

            # wrap the usage parts if it's too long
            text_width = self._width - self._current_indent
            if len(prefix) + len(self._decolor(usage)) > text_width:

                # break usage into wrappable parts
                opt_parts = parts[:pos_start]
                pos_parts = parts[pos_start:]

                # helper for wrapping lines
                def get_lines(parts, indent, prefix=None):
                    lines = []
                    line = []
                    indent_length = len(indent)
                    if prefix is not None:
                        line_len = len(prefix) - 1
                    else:
                        line_len = indent_length - 1
                    for part in parts:
                        part_len = len(self._decolor(part))
                        if line_len + 1 + part_len > text_width and line:
                            lines.append(indent + ' '.join(line))
                            line = []
                            line_len = indent_length - 1
                        line.append(part)
                        line_len += part_len + 1
                    if line:
                        lines.append(indent + ' '.join(line))
                    if prefix is not None:
                        lines[0] = lines[0][indent_length:]
                    return lines

                # if prog is short, follow it with optionals or positionals
                prog_len = len(self._decolor(prog))
                if len(prefix) + prog_len <= 0.75 * text_width:
                    indent = ' ' * (len(prefix) + prog_len + 1)
                    if opt_parts:
                        lines = get_lines([prog] + opt_parts, indent, prefix)
                        lines.extend(get_lines(pos_parts, indent))
                    elif pos_parts:
                        lines = get_lines([prog] + pos_parts, indent, prefix)
                    else:
                        lines = [prog]

                # if prog is long, put it on its own line
                else:
                    indent = ' ' * len(prefix)
                    parts = opt_parts + pos_parts
                    lines = get_lines(parts, indent)
                    if len(lines) > 1:
                        lines = []
                        lines.extend(get_lines(opt_parts, indent))
                        lines.extend(get_lines(pos_parts, indent))
                    lines = [prog] + lines

                # join lines into usage
                usage = '\n'.join(lines)

            usage = usage.removeprefix(prog)
            usage = f"{t.prog}{prog}{t.reset}{usage}"

        # prefix with 'usage:'
        return f'{t.usage}{prefix}{t.reset}{usage}\n\n'