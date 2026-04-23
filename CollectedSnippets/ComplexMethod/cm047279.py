def _compile_directive_set(self, el, compile_context, level):
        """Compile `t-set` expressions into a python code as a list of
        strings.

        There are 3 kinds of `t-set`:
        * `t-value` containing python code;
        * `t-valuef` containing strings to format;
        * `t-valuef.translate` containing translated strings to format;
        * whose value is the content of the tag (being Markup safe).

        The code will contain the assignment of the dynamically generated value.
        """

        code = self._flush_text(compile_context, level, rstrip=el.tag.lower() == 't')

        if 't-set' in el.attrib:
            varname = el.attrib.pop('t-set')
            if varname == "":
                raise KeyError('t-set')
            if varname != T_CALL_SLOT and varname[0] != '{' and not VARNAME_REGEXP.match(varname):
                raise SyntaxError('The varname can only contain alphanumeric characters and underscores.')
            if '__' in varname:
                raise SyntaxError(f"Using variable names with '__' is not allowed: {varname!r}")

            if 't-value' in el.attrib or 't-valuef' in el.attrib or 't-valuef.translate' in el.attrib or varname[0] == '{':
                el.attrib.pop('t-inner-content') # The content is considered empty.
                if varname == T_CALL_SLOT:
                    raise SyntaxError('t-set="0" should not be set from t-value or t-valuef')

            if 't-value' in el.attrib:
                expr = el.attrib.pop('t-value') or 'None'
                code.append(indent_code(f"values[{varname!r}] = {self._compile_expr(expr)}", level))
            elif 't-valuef' in el.attrib:
                exprf = el.attrib.pop('t-valuef')
                code.append(indent_code(f"values[{varname!r}] = {self._compile_format(exprf)}", level))
            elif 't-valuef.translate' in el.attrib:
                exprf = el.attrib.pop('t-valuef.translate')
                if self.env.context.get('edit_translations'):
                    code.append(indent_code(f"values[{varname!r}] = Markup({self._compile_format(exprf)})", level))
                else:
                    code.append(indent_code(f"values[{varname!r}] = {self._compile_format(exprf)}", level))
            elif varname[0] == '{':
                code.append(indent_code(f"values.update({self._compile_expr(varname)})", level))
            else:
                # set the content as value
                _ref, path, xml = compile_context['_qweb_error_path_xml']
                content = (
                    self._compile_directive(el, compile_context, 'inner-content', 1) +
                    self._flush_text(compile_context, 1))
                if content:
                    def_name = compile_context['make_name']('t_set')
                    def_code = [f"def {def_name}(self, values):"]
                    def_code.append(indent_code(f'# element: {path!r} , {xml!r}', 1))
                    def_code.extend(content)
                    compile_context['template_functions'][def_name] = def_code

                    code.append(indent_code(f"""
                        values[{varname!r}] = QwebContent(self, QwebCallParameters(self.env.context, {compile_context['ref']!r}, {def_name!r}, values.copy(), 'root', 't-set', (template_options['ref'], {path!r}, {xml!r})))
                    """, level))
                else:
                    code.append(indent_code(f"values[{varname!r}] = ''", level))

        return code