def _compile_node(self, el, compile_context, level):
        """ Compile the given element into python code.

            The t-* attributes (directives) will be converted to a python instruction. If there
            are no t-* attributes, the element will be considered static.

            Directives are compiled using the order provided by the
            ``_directives_eval_order`` method (an create the
            ``compile_context['iter_directives']`` iterator).
            For compilation, the directives supported are those with a
            compilation method ``_compile_directive_*``

        :return: list of string
        """
        # Internal directive used to skip a rendering.
        if 't-qweb-skip' in el.attrib:
            return []

        # if tag don't have qweb attributes don't use directives
        if self._is_static_node(el, compile_context):
            return self._compile_static_node(el, compile_context, level)

        path = compile_context['root'].getpath(el)
        xml = etree.tostring(etree.Element(el.tag, el.attrib), encoding='unicode')
        compile_context['_qweb_error_path_xml'][0] = compile_context['ref']
        compile_context['_qweb_error_path_xml'][1] = path
        compile_context['_qweb_error_path_xml'][2] = xml
        body = [indent_code(f'# element: {path!r} , {xml!r}', level)]

        # create an iterator on directives to compile in order
        compile_context['iter_directives'] = iter(self._directives_eval_order())

        # add technical directive tag-open, tag-close, inner-content and take
        # care of the namspace
        if not el.nsmap:
            unqualified_el_tag = el_tag = el.tag
        else:
            # Etree will remove the ns prefixes indirection by inlining the corresponding
            # nsmap definition into the tag attribute. Restore the tag and prefix here.
            # Note: we do not support namespace dynamic attributes, we need a default URI
            # on the root and use attribute directive t-att="{'xmlns:example': value}".
            unqualified_el_tag = etree.QName(el.tag).localname
            el_tag = unqualified_el_tag
            if el.prefix:
                el_tag = f'{el.prefix}:{el_tag}'

        if unqualified_el_tag != 't':
            el.set('t-tag-open', el_tag)
            if el_tag not in VOID_ELEMENTS:
                el.set('t-tag-close', el_tag)

        if not ({'t-out', 't-esc', 't-raw', 't-field'} & set(el.attrib)):
            el.set('t-inner-content', 'True')

        return body + self._compile_directives(el, compile_context, level)