def _compile_directive_call(self, el, compile_context, level):
        """Compile `t-call` expressions into a python code as a list of
        strings.

        `t-call` allow formating string dynamic at rendering time.
        Can use `t-options` used to call and render the sub-template at
        rendering time.
        The sub-template is called with a copy of the rendering values
        dictionary. The dictionary contains the key 0 coming from the
        compilation of the contents of this element

        The code will contain the call of the template and a function from the
        compilation of the content of this element.
        """
        expr = el.attrib.pop('t-call')

        el_tag = etree.QName(el.tag).localname if el.nsmap else el.tag
        if el_tag != 't':
            raise SyntaxError(f"t-call must be on a <t> element (actually on <{el_tag}>).")

        if el.attrib.get('t-call-options'): # retro-compatibility
            el.attrib.set('t-options', el.attrib.pop('t-call-options'))

        nsmap = compile_context.get('nsmap')

        code = self._flush_text(compile_context, level, rstrip=el.tag.lower() == 't')
        _ref, path, xml = compile_context['_qweb_error_path_xml']

        # options
        el.attrib.pop('t-consumed-options', None)
        code.append(indent_code("t_call_options = values.pop('__qweb_options__', {})", level))
        if nsmap:
            # update this dict with the current nsmap so that the callee know
            # if he outputting the xmlns attributes is relevenat or not
            nsmap = []
            for key, value in compile_context['nsmap'].items():
                if isinstance(key, str):
                    nsmap.append(f'{key!r}:{value!r}')
                else:
                    nsmap.append(f'None:{value!r}')
            code.append(indent_code(f"t_call_options.update(nsmap={{{', '.join(nsmap)}}})", level))

        # values from content (t-out="0")
        if bool(list(el) or el.text):
            is_deprecated_version = not any(not key.startswith('t-') for key in el.attrib) and any(n.attrib.get('t-set') for n in el)

            def_name = compile_context['make_name']('t_call')
            code_content = [f"def {def_name}(self, values):"]
            code_content.append(indent_code(f'# element: {path!r} , {xml!r}', 1))
            code_content.extend(self._compile_directive(el, compile_context, 'inner-content', 1))
            self._append_text('', compile_context)  # To ensure the template function is a generator and doesn't become a regular function
            code_content.extend(self._flush_text(compile_context, 1, rstrip=True))

            compile_context['template_functions'][def_name] = code_content

            code.append(indent_code(f"""
                t_call_content_values = values.copy()
                qwebContent = QwebContent(self, QwebCallParameters(self.env.context, {compile_context['ref']!r}, {def_name!r}, t_call_content_values, 'root', 'inner-content', (template_options['ref'], {path!r}, {xml!r})))
                t_call_values = {{ {T_CALL_SLOT}: qwebContent}}
            """, level))

            if is_deprecated_version:
                # force the loading of the content to get values from t-set
                code.append(indent_code(f"""
                    str(qwebContent)
                    new_values = {{k: v for k, v in t_call_content_values.items() if k != {T_CALL_SLOT} and k != '__qweb_attrs__' and values.get(k) is not v}}
                    t_call_values.update(new_values)
                """, level))
        else:
            code.append(indent_code(f"t_call_values = {{ {T_CALL_SLOT}: '' }}", level))

        # args to values
        for key in list(el.attrib):
            if key.endswith('.f'):
                name = key.removesuffix(".f")
                value = el.attrib.pop(key)
                code.append(indent_code(f"t_call_values[{name!r}] = {self._compile_format(value)}", level))
            elif key.endswith('.translate'):
                name = key.removesuffix(".f").removesuffix(".translate")
                value = el.attrib.pop(key)
                if self.env.context.get('edit_translations'):
                    code.append(indent_code(f"t_call_values[{name!r}] = Markup({self._compile_format(value)})", level))
                else:
                    code.append(indent_code(f"t_call_values[{name!r}] = {self._compile_format(value)}", level))
            elif not key.startswith('t-'):
                value = el.attrib.pop(key)
                code.append(indent_code(f"t_call_values[{key!r}] = {self._compile_expr(value)}", level))
            elif key == 't-args':
                value = el.attrib.pop(key)
                code.append(indent_code(f"""
                    atts_value = {self._compile_expr(value)}
                    if isinstance(atts_value, dict):
                        t_call_values.update(atts_value)
                    elif isinstance(atts_value, (list, tuple)) and not isinstance(atts_value[0], (list, tuple)):
                        t_call_values.update([atts_value])
                    elif isinstance(atts_value, (list, tuple)):
                        t_call_values.update(dict(atts_value))
                    """, level))

        template = expr if expr.isnumeric() else self._compile_format(expr)

        # call
        code.append(indent_code(f"""
            template = {template}
            """, level))
        if '%' in template:
            code.append(indent_code("""
                if template.isnumeric():
                    template = int(template)
                """, level))

        code.append(indent_code(f"yield QwebCallParameters(t_call_options, template, None, t_call_values, True, 't-call', (template_options['ref'], {path!r}, {xml!r}))", level))

        return code