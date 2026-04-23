def _compile_static_node(self, el, compile_context, level):
        """ Compile a purely static element into a list of string. """
        if not el.nsmap:
            unqualified_el_tag = el_tag = el.tag
            attrib = self._post_processing_att(el.tag, {**el.attrib, '__is_static_node': True})
        else:
            # Etree will remove the ns prefixes indirection by inlining the corresponding
            # nsmap definition into the tag attribute. Restore the tag and prefix here.
            unqualified_el_tag = etree.QName(el.tag).localname
            el_tag = unqualified_el_tag
            if el.prefix:
                el_tag = f'{el.prefix}:{el_tag}'

            attrib = {}
            # If `el` introduced new namespaces, write them as attribute by using the
            # `attrib` dict.
            for ns_prefix, ns_definition in set(el.nsmap.items()) - set(compile_context['nsmap'].items()):
                if ns_prefix is None:
                    attrib['xmlns'] = ns_definition
                else:
                    attrib[f'xmlns:{ns_prefix}'] = ns_definition

            # Etree will also remove the ns prefixes indirection in the attributes. As we only have
            # the namespace definition, we'll use an nsmap where the keys are the definitions and
            # the values the prefixes in order to get back the right prefix and restore it.
            ns = chain(compile_context['nsmap'].items(), el.nsmap.items())
            nsprefixmap = {v: k for k, v in ns}
            for key, value in el.attrib.items():
                name = key.removesuffix(".translate")
                attrib_qname = etree.QName(name)
                if attrib_qname.namespace:
                    attrib[f'{nsprefixmap[attrib_qname.namespace]}:{attrib_qname.localname}'] = value
                else:
                    attrib[name] = value

            attrib = self._post_processing_att(el.tag, {**attrib, '__is_static_node': True})

            # Update the dict of inherited namespaces before continuing the recursion. Note:
            # since `compile_context['nsmap']` is a dict (and therefore mutable) and we do **not**
            # want changes done in deeper recursion to bevisible in earlier ones, we'll pass
            # a copy before continuing the recursion and restore the original afterwards.
            original_nsmap = dict(compile_context['nsmap'])

        if unqualified_el_tag != 't':
            attributes = ''.join(f' {name.removesuffix(".translate")}="{escape(str(value))}"'
                                for name, value in attrib.items() if value or isinstance(value, str))
            self._append_text(f'<{el_tag}{"".join(attributes)}', compile_context)
            if el_tag in VOID_ELEMENTS:
                self._append_text('/>', compile_context)
            else:
                self._append_text('>', compile_context)

        el.attrib.clear()

        if el.nsmap:
            compile_context['nsmap'].update(el.nsmap)
            body = self._compile_directive(el, compile_context, 'inner-content', level)
            compile_context['nsmap'] = original_nsmap
        else:
            body = self._compile_directive(el, compile_context, 'inner-content', level)

        if unqualified_el_tag != 't':
            if el_tag not in VOID_ELEMENTS:
                self._append_text(f'</{el_tag}>', compile_context)

        return body