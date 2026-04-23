def _compile_directive_att(self, el, compile_context, level):
        """ Compile the attributes of the given elements.

        The compiled function will create the ``values['__qweb_attrs__']``
        dictionary. Then the dictionary will be output.


        The new namespaces of the current element.

        The static attributes (not prefixed by ``t-``) are add to the
        dictionary in first.

        The dynamic attributes values will be add after. The dynamic
        attributes has different origins.

        - value from key equal to ``t-att``: python dictionary expression;
        - value from keys that start with ``t-att-``: python expression;
        - value from keys that start with ``t-attf-``: format string
            expression.
        """
        code = [indent_code("attrs = values['__qweb_attrs__'] = {}", level)]

        # Compile the introduced new namespaces of the given element.
        #
        # Add the found new attributes into the `attrs` dictionary like
        # the static attributes.
        if el.nsmap:
            for ns_prefix, ns_definition in set(el.nsmap.items()) - set(compile_context['nsmap'].items()):
                key = 'xmlns'
                if ns_prefix is not None:
                    key = f'xmlns:{ns_prefix}'
                code.append(indent_code(f'attrs[{key!r}] = {ns_definition!r}', level))

        # Compile the static attributes of the given element.
        #
        # Etree will also remove the ns prefixes indirection in the
        # attributes. As we only have the namespace definition, we'll use
        # an nsmap where the keys are the definitions and the values the
        # prefixes in order to get back the right prefix and restore it.
        if any(not key.startswith('t-') for key in el.attrib):
            nsprefixmap = {v: k for k, v in chain(compile_context['nsmap'].items(), el.nsmap.items())}
            for key in list(el.attrib):
                if not key.startswith('t-'):
                    value = el.attrib.pop(key)
                    name = key.removesuffix(".translate")
                    attrib_qname = etree.QName(name)
                    if attrib_qname.namespace:
                        name = f'{nsprefixmap[attrib_qname.namespace]}:{attrib_qname.localname}'
                    code.append(indent_code(f'attrs[{name!r}] = {value!r}', level))

        # Compile the dynamic attributes of the given element. All
        # attributes will be add to the ``attrs`` dictionary in the
        # compiled function.
        for key in list(el.attrib):
            if key.startswith('t-attf-'):
                value = el.attrib.pop(key)
                name = key[7:].removesuffix(".translate")
                code.append(indent_code(f"attrs[{name!r}] = {self._compile_format(value)}", level))
            elif key.startswith('t-att-'):
                value = el.attrib.pop(key)
                code.append(indent_code(f"attrs[{key[6:]!r}] = {self._compile_expr(value)}", level))
            elif key == 't-att':
                value = el.attrib.pop(key)
                code.append(indent_code(f"""
                    atts_value = {self._compile_expr(value)}
                    if isinstance(atts_value, dict):
                        attrs.update(atts_value)
                    elif isinstance(atts_value, (list, tuple)) and not isinstance(atts_value[0], (list, tuple)):
                        attrs.update([atts_value])
                    elif isinstance(atts_value, (list, tuple)):
                        attrs.update(dict(atts_value))
                    """, level))

        return code