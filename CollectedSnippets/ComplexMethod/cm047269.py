def _get_error_info(self, error, stack: list[QwebStackFrame], frame: QwebStackFrame) -> QWebErrorInfo:
        no_id_ref = 'etree._Element'

        path = None
        html = None
        loaded_codes = self.env.context['__qweb_loaded_codes']
        if (frame.params.view_ref in loaded_codes and not isinstance(error, RecursionError)) or len(stack) <= 1:
            options = frame.options or {}  # The compilation may have failed before the compilation options were loaded.
            if 'ref' not in options:
                options = self.env.context['__qweb_loaded_options'].get(frame.params.view_ref) or {}
            ref = options.get('ref') or frame.params.view_ref  # The template can have a null reference, for example for a provided etree.
            ref_name = options.get('ref_name') or None
            code = loaded_codes.get(frame.params.view_ref) or loaded_codes.get(no_id_ref)
            if ref == self.env.context['_qweb_error_path_xml'][0]:
                path = self.env.context['_qweb_error_path_xml'][1]
                html = self.env.context['_qweb_error_path_xml'][2]
        else:
            # get the previous caller (like t-call) to display erroneous xml node.
            options = stack[-2].options or {}  # The compilation may have failed before the compilation options were loaded.
            ref = options.get('ref')
            ref_name = options.get('ref_name')
            code = loaded_codes.get(ref) or loaded_codes.get(no_id_ref)
            if frame.params.path_xml:
                path = frame.params.path_xml[1]
                html = frame.params.path_xml[2]

        source_file_ref = None if ref == no_id_ref else ref
        line_nb = 0
        trace = traceback.format_exc()
        for error_line in reversed(trace.split('\n')):
            if f'File "<{source_file_ref}>"' in error_line or (ref is None and 'File "<' in error_line):
                line_function = error_line.split(', line ')[1]
                line_nb = int(line_function.split(',')[0])
                break

        source = [info.params.path_xml for info in stack if info.params.path_xml]
        code_lines = (code or '').split('\n')

        found = False
        for code_line in reversed(code_lines[:line_nb]):
            if code_line.startswith('def '):
                break
            match = re.match(r'\s*# element: (.*) , (.*)', code_line)
            if not match:
                if found:
                    break
                continue
            if found:
                info = (ref, match[1][1:-1], match[2][1:-1])
                if info not in source:
                    source.append(info)
            else:
                found = True
                path = match[1][1:-1]
                html = match[2][1:-1]

        if path:
            source.append((ref, path, html))

        surrounding = None
        if self.env.context.get('dev_mode') and line_nb:
            if html and ' t-if=' in html and ' if ' in '\n'.join(code_lines[line_nb - 2:line_nb - 1]):
                line_nb -= 1
            previous_lines = '\n'.join(code_lines[max(line_nb - 25, 0):line_nb - 1])
            line = code_lines[line_nb - 1]
            next_lines = '\n'.join(code_lines[line_nb:line_nb + 5])
            indent = re.search(r"^(\s*)", line).group(0)
            surrounding = textwrap.indent(
                textwrap.dedent(
                    f"{previous_lines}\n"
                    f"{indent}########### Line triggering the error ############\n{line}\n"
                    f"{indent}##################################################\n{next_lines}"
                ),
                ' ' * 8
            )

        return QWebErrorInfo(f'{error.__class__.__name__}: {error}', ref if ref_name is None else ref_name, ref, path, html, source, surrounding)