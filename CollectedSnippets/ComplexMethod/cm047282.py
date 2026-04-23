def _compile_directive_out(self, el, compile_context, level):
        """Compile `t-out` expressions into a python code as a list of
        strings.

        The code will contain evalution and rendering of the compiled value. If
        the compiled value is None or False, the tag is not added to the render
        (Except if the widget forces rendering or there is default content).
        (eg: `<t t-out="my_value">Default content if falsy</t>`)

        The output can have some rendering option with `t-options-widget` or
        `t-options={'widget': ...}. At rendering time, The compiled code will
        call ``_get_widget`` method or ``_get_field`` method for `t-field`.

        A `t-field` will necessarily be linked to the value of a record field
        (eg: `<span t-field="record.field_name"/>`), a t-out` can be applied
        to any value (eg: `<span t-out="10" t-options-widget="'float'"/>`).
        """
        ttype = 't-out'
        expr = el.attrib.pop('t-out', None)
        if expr is None:
            ttype = 't-field'
            expr = el.attrib.pop('t-field', None)
            if expr is None:
                # deprecated use.
                ttype = 't-esc'
                expr = el.attrib.pop('t-esc', None)
                if expr is None:
                    ttype = 't-raw'
                    expr = el.attrib.pop('t-raw')

        code = self._flush_text(compile_context, level)

        _ref, path, xml = compile_context['_qweb_error_path_xml']

        code_options = el.attrib.pop('t-consumed-options', 'None')
        tag_open = (
            self._compile_directive(el, compile_context, 'tag-open', level + 1) +
            self._flush_text(compile_context, level + 1))
        tag_close = (
            self._compile_directive(el, compile_context, 'tag-close', level + 1) +
            self._flush_text(compile_context, level + 1))
        default_body = (
            self._compile_directive(el, compile_context, 'inner-content', level + 1) +
            self._flush_text(compile_context, level + 1))

        # The generated code will set the values of the content, attrs (used to
        # output attributes) and the force_display (if the widget or field
        # mark force_display as True, the tag will be inserted in the output
        # even the value of content is None and without default value)

        if expr == T_CALL_SLOT and code_options != 'True':
            code.append(indent_code("if True:", level))
            code.extend(tag_open)
            code.append(indent_code(f"yield values.get({T_CALL_SLOT}, '')", level + 1))
            code.extend(tag_close)
            return code
        elif ttype == 't-field':
            record, field_name = expr.rsplit('.', 1)
            code.append(indent_code(f"""
                field_attrs, content, force_display = self._get_field({self._compile_expr(record, raise_on_missing=True)}, {field_name!r}, {expr!r}, {el.tag!r}, values.pop('__qweb_options__', {{}}), values)
                if values.get('__qweb_attrs__') is None:
                    values['__qweb_attrs__'] = field_attrs
                else:
                    values['__qweb_attrs__'].update(field_attrs)
                if content is not None and content is not False:
                    content = self._compile_to_str(content)
                """, level))
            force_display_dependent = True
        else:
            if expr == T_CALL_SLOT:
                code.append(indent_code(f"content = values.get({T_CALL_SLOT}, '')", level))
            else:
                code.append(indent_code(f"content = {self._compile_expr(expr)}", level))

            if code_options == 'True':
                code.append(indent_code(f"""
                    widget_attrs, content, force_display = self._get_widget(content, {expr!r}, {el.tag!r}, values.pop('__qweb_options__', {{}}), values)
                    if values.get('__qweb_attrs__') is None:
                        values['__qweb_attrs__'] = widget_attrs
                    else:
                        values['__qweb_attrs__'].update(widget_attrs)
                    content = self._compile_to_str(content)
                    """, level))
                force_display_dependent = True
            else:
                force_display_dependent = False

            if ttype == 't-raw':
                # deprecated use.
                code.append(indent_code("""
                    if content is not None and content is not False:
                        content = Markup(content)
                """, level))

        # The generated code will create the output tag with all attribute.
        # If the value is not falsy or if there is default content or if it's
        # in force_display mode, the tag is add into the output.

        el.attrib.pop('t-tag', None) # code generating the output is done here

        # generate code to display the tag if the value is not Falsy

        code.append(indent_code("if content is not None and content is not False:", level))
        code.extend(tag_open)
        # Use str to avoid the escaping of the other html content because the
        # yield generator MarkupSafe values will be join into an string in
        # `_render`.
        code.append(indent_code(f"""
            if isinstance(content, QwebContent):
                self.env.context['_qweb_error_path_xml'][0] = template_options['ref']
                self.env.context['_qweb_error_path_xml'][1] = {path!r}
                self.env.context['_qweb_error_path_xml'][2] = {xml!r}
                yield content
            else:
                yield str(escape(content))
        """, level + 1))
        code.extend(tag_close)

        # generate code to display the tag with default content if the value is
        # Falsy

        if default_body or compile_context['_text_concat']:
            _text_concat = list(compile_context['_text_concat'])
            compile_context['_text_concat'].clear()
            code.append(indent_code("else:", level))
            code.extend(tag_open)
            code.extend(default_body)
            compile_context['_text_concat'].extend(_text_concat)
            code.extend(tag_close)
        elif force_display_dependent:

            # generate code to display the tag if it's the force_diplay mode.

            if tag_open + tag_close:
                code.append(indent_code("elif force_display:", level))
                code.extend(tag_open + tag_close)

            code.append(indent_code("""else: values.pop('__qweb_attrs__', None)""", level))

        return code