def _compile_directive_inner_content(self, el, compile_context, level):
        """Compiles the content of the element (is the technical `t-inner-content`
        directive created by QWeb) into a python code as a list of
        strings.

        The code will contains the text content of the node or the compliled
        code from the recursive call of ``_compile_node``.
        """
        el.attrib.pop('t-inner-content', None)

        if el.nsmap:
            # Update the dict of inherited namespaces before continuing the recursion. Note:
            # since `compile_context['nsmap']` is a dict (and therefore mutable) and we do **not**
            # want changes done in deeper recursion to bevisible in earlier ones, we'll pass
            # a copy before continuing the recursion and restore the original afterwards.
            compile_context = dict(compile_context, nsmap=el.nsmap)

        if el.text is not None:
            self._append_text(el.text, compile_context)
        body = []
        for item in list(el):
            if isinstance(item, etree._Comment):
                if compile_context.get('preserve_comments'):
                    self._append_text(f"<!--{item.text}-->", compile_context)
            elif isinstance(item, etree._ProcessingInstruction):
                if compile_context.get('preserve_comments'):
                    self._append_text(f"<?{item.target} {item.text}?>", compile_context)
            else:
                body.extend(self._compile_node(item, compile_context, level))
            # comments can also contains tail text
            if item.tail is not None:
                self._append_text(item.tail, compile_context)
        return body