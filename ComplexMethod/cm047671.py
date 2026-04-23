def translatable(node, force_inline=False):
        """ Return whether the given node can be translated as a whole. """
        # Some specific nodes (e.g., text highlights) have an auto-updated DOM
        # structure that makes them impossible to translate.
        # The introduction of a translation `<span>` in the middle of their
        # hierarchy breaks their functionalities. We need to force them to be
        # translated as a whole using the `o_translate_inline` class.
        force_inline = force_inline or is_force_inline(node)
        return (
            (force_inline or node.tag in TRANSLATED_ELEMENTS)
            # Nodes with directives are not translatable. Directives usually
            # start with `t-`, but this prefix is optional for `groups` (see
            # `_compile_directive_groups` which reads `t-groups` and `groups`)
            and not any(key.startswith("t-") or key == 'groups' or key.endswith(".translate") for key in node.attrib)
            and all(translatable(child, force_inline) for child in node)
        )