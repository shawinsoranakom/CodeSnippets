def hastext(node, pos=0, force_inline=False):
        """ Return whether the given node contains some text to translate at the
            given child node position.  The text may be before the child node,
            inside it, or after it.
        """
        force_inline = force_inline or is_force_inline(node)
        return (
            # there is some text before node[pos]
            nonspace(node[pos-1].tail if pos else node.text)
            or (
                pos < len(node)
                and translatable(node[pos], force_inline)
                and (
                    any(  # attribute to translate
                        val and (
                            is_translatable_attrib(key, node) or
                            (key == 'value' and is_translatable_attrib_value(node[pos])) or
                            (key == 'text' and is_translatable_attrib_text(node[pos]))
                        )
                        for key, val in node[pos].attrib.items()
                    )
                    # node[pos] contains some text to translate
                    or hastext(node[pos], 0, force_inline)
                    # node[pos] has no text, but there is some text after it
                    or hastext(node, pos + 1, force_inline)
                )
            )
        )