def _compile_node(self, el, compile_context, level):
        snippet_key = compile_context.get('snippet-key')

        template = compile_context['ref_name']
        sub_call_key = compile_context.get('snippet-sub-call-key')

        # We only add the 'data-snippet' & 'data-name' attrib once when
        # compiling the root node of the template.
        if not template or template not in {snippet_key, sub_call_key} or el.getparent() is not None:
            return super()._compile_node(el, compile_context, level)

        snippet_base_node = el
        if el.tag == 't':
            el_children = [child for child in list(el) if isinstance(child.tag, str) and child.tag != 't']
            if len(el_children) == 1:
                snippet_base_node = el_children[0]
            elif not el_children:
                # If there's not a valid base node we check if the base node is
                # a t-call to another template. If so the called template's base
                # node must take the current snippet key.
                el_children = [child for child in list(el) if isinstance(child.tag, str)]
                if len(el_children) == 1:
                    sub_call = el_children[0].get('t-call')
                    if sub_call:
                        el_children[0].set('t-options', f"{{'snippet-key': '{snippet_key}', 'snippet-sub-call-key': '{sub_call}'}}")
        # If it already has a data-snippet it is a saved or an
        # inherited snippet. Do not override it.
        if 'data-snippet' not in snippet_base_node.attrib:
            snippet_base_node.attrib['data-snippet'] = \
                snippet_key.split('.', 1)[-1]
        # If it already has a data-name it is a saved or an
        # inherited snippet. Do not override it.
        snippet_name = compile_context.get('snippet-name')
        if snippet_name and 'data-name' not in snippet_base_node.attrib:
            snippet_base_node.attrib['data-name'] = snippet_name
        return super()._compile_node(el, compile_context, level)