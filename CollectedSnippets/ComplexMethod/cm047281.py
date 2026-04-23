def _compile_directive_if(self, el, compile_context, level):
        """Compile `t-if` expressions into a python code as a list of strings.

        The code will contain the condition `if`, `else` and `elif` part that
        wrap the rest of the compiled code of this element.
        """
        expr = el.attrib.pop('t-if', el.attrib.pop('t-elif', None))

        assert not expr.isspace(), 't-if or t-elif expression should not be empty.'

        strip = self._rstrip_text(compile_context)  # the withspaces is visible only when display a content
        if el.tag.lower() == 't' and el.text and LSTRIP_REGEXP.search(el.text):
            strip = ''  # remove technical spaces
        code = self._flush_text(compile_context, level)

        code.append(indent_code(f"if {self._compile_expr(expr)}:", level))
        body = []
        if strip:
            self._append_text(strip, compile_context)
        body.extend(
            self._compile_directives(el, compile_context, level + 1) +
            self._flush_text(compile_context, level + 1, rstrip=True))
        code.extend(body or [indent_code('pass', level + 1)])

        # Look for the else or elif conditions
        next_el = el.getnext()
        comments_to_remove = []
        while isinstance(next_el, etree._Comment):
            comments_to_remove.append(next_el)
            next_el = next_el.getnext()

        # If there is a t-else directive, the comment nodes are deleted
        # and the t-else or t-elif is validated.
        if next_el is not None and {'t-else', 't-elif'} & set(next_el.attrib):
            # Insert a flag to allow t-else or t-elif rendering.
            next_el.attrib['t-else-valid'] = 'True'

            # remove comment node
            parent = el.getparent()
            for comment in comments_to_remove:
                parent.remove(comment)
            if el.tail and not el.tail.isspace():
                raise SyntaxError("Unexpected non-whitespace characters between t-if and t-else directives")
            el.tail = None

            # You have to render the `t-else` and `t-elif` here in order
            # to be able to put the log. Otherwise, the parent's
            # `t-inner-content`` directive will render the different
            # nodes without taking indentation into account such as:
            #    if (if_expression):
            #         content_if
            #    log ['last_path_node'] = path
            #    else:
            #       content_else

            code.append(indent_code("else:", level))
            body = []
            if strip:
                self._append_text(strip, compile_context)
            body.extend(
                self._compile_node(next_el, compile_context, level + 1)+
                self._flush_text(compile_context, level + 1, rstrip=True))
            code.extend(body or [indent_code('pass', level + 1)])

            # Insert a flag to avoid the t-else or t-elif rendering when
            # the parent t-inner-content dirrective compile his
            # children.
            next_el.attrib['t-qweb-skip'] = 'True'

        return code