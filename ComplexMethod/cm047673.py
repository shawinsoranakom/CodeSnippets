def process(node):
        """ Translate the given node. """
        if (
            isinstance(node, SKIPPED_ELEMENT_TYPES)
            or node.tag in SKIPPED_ELEMENTS
            or node.get('t-translation', "").strip() == "off"
            or node.tag == 'attribute' and node.get('name') not in ('value', 'text') and not is_translatable_attrib(node.get('name'), node)
            or node.getparent() is None and avoid_pattern.match(node.text or "")
        ):
            return

        pos = 0
        while True:
            # check for some text to translate at the given position
            if hastext(node, pos):
                # move all translatable children nodes from the given position
                # into a <div> element
                div = etree.Element('div')
                div.text = (node[pos-1].tail if pos else node.text) or ''
                while pos < len(node) and translatable(node[pos], is_force_inline(node)):
                    div.append(node[pos])

                # translate the content of the <div> element as a whole
                content = serialize(div)[5:-6]
                original = content.strip()
                translated = callback(original)
                if translated:
                    result = content.replace(original, translated)
                    # <div/> is used to auto fix crapy result
                    result_elem = parse_html(f"<div>{result}</div>")
                    # change the tag to <span/> which is one of TRANSLATED_ELEMENTS
                    # so that 'result_elem' can be checked by translatable and hastext
                    result_elem.tag = 'span'
                    if translatable(result_elem) and hastext(result_elem):
                        div = result_elem
                        if pos:
                            node[pos-1].tail = div.text
                        else:
                            node.text = div.text

                # move the content of the <div> element back inside node
                while len(div) > 0:
                    node.insert(pos, div[0])
                    pos += 1

            if pos >= len(node):
                break

            # node[pos] is not translatable as a whole, process it recursively
            process(node[pos])
            pos += 1

        # translate the attributes of the node
        for key, val in node.attrib.items():
            if nonspace(val):
                if (
                    is_translatable_attrib(key, node) or
                    (key == 'value' and is_translatable_attrib_value(node)) or
                    (key == 'text' and is_translatable_attrib_text(node))
                ):
                    if key.startswith('t-'):
                        value = translate_format_string_expression(val.strip(), callback)
                    else:
                        value = callback(val.strip())
                    node.set(key, value or val)