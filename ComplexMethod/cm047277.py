def _compile_directives(self, el, compile_context, level):
        """ Compile the given element, following the directives given in the
        iterator ``compile_context['iter_directives']`` create by
        `_compile_node`` method.

        :return: list of code lines
        """
        if self._is_static_node(el, compile_context):
            el.attrib.pop('t-tag-open', None)
            el.attrib.pop('t-inner-content', None)
            el.attrib.pop('t-tag-close', None)
            return self._compile_static_node(el, compile_context, level)

        code = []

        # compile the directives still present on the element
        for directive in compile_context['iter_directives']:
            if ('t-' + directive) in el.attrib:
                code.extend(self._compile_directive(el, compile_context, directive, level))
            elif directive == 'groups':
                if directive in el.attrib:
                    code.extend(self._compile_directive(el, compile_context, directive, level))
            elif directive == 'att':
                code.extend(self._compile_directive(el, compile_context, directive, level))
            elif directive == 'options':
                if any(name.startswith('t-options-') for name in el.attrib):
                    code.extend(self._compile_directive(el, compile_context, directive, level))

        # compile unordered directives still present on the element
        for att in el.attrib:
            if att not in SPECIAL_DIRECTIVES and att.startswith('t-') and getattr(self, f"_compile_directive_{att[2:].replace('-', '_')}", None):
                code.extend(self._compile_directive(el, compile_context, directive, level))

        remaining = set(el.attrib) - SPECIAL_DIRECTIVES
        if remaining:
            _logger.warning('Unknown directives or unused attributes: %s in %s', remaining, compile_context['template'])

        return code