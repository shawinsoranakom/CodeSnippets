def _test_modifiers(what, expected_vnames):
            if isinstance(what, dict):
                node = etree.Element('field', {k: str(v) for k, v in what.items()})
            else:
                node = etree.fromstring(what) if isinstance(what, str) else what
            modifiers = {attr: node.attrib[attr] for attr in node.attrib if attr in ir_ui_view.VIEW_MODIFIERS}
            vnames = set()
            for expr in modifiers.values():
                vnames |= view_validation.get_expression_field_names(expr) - {'id'}
            assert vnames == expected_vnames, f"{vnames!r} != {expected_vnames!r}"