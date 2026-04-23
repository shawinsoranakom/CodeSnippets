def get_view_arch_from_file(filepath, xmlid):
    module, view_id = xmlid.split('.')

    xpath = f"//*[@id='{xmlid}' or @id='{view_id}']"
    # when view is created from model with inheritS of ir_ui_view, the
    # xmlid has been suffixed by '_ir_ui_view'. We need to also search
    # for views without this prefix.
    if view_id.endswith('_ir_ui_view'):
        # len('_ir_ui_view') == 11
        xpath = xpath[:-1] + f" or @id='{xmlid[:-11]}' or @id='{view_id[:-11]}']"

    document = etree.parse(filepath)
    for node in document.xpath(xpath):
        if node.tag == 'record':
            field_arch = node.find('field[@name="arch"]')
            if field_arch is not None:
                _fix_multiple_roots(field_arch)
                inner = ''.join(
                    etree.tostring(child, encoding='unicode')
                    for child in field_arch.iterchildren()
                )
                return field_arch.text + inner

            field_view = node.find('field[@name="view_id"]')
            if field_view is not None:
                ref_module, _, ref_view_id = field_view.attrib.get('ref').rpartition('.')
                ref_xmlid = f'{ref_module or module}.{ref_view_id}'
                return get_view_arch_from_file(filepath, ref_xmlid)

            return None

        elif node.tag == 'template':
            # The following dom operations has been copied from convert.py's _tag_template()
            if not node.get('inherit_id'):
                node.set('t-name', xmlid)
                node.tag = 't'
            else:
                node.tag = 'data'
            node.attrib.pop('id', None)
            return etree.tostring(node, encoding='unicode')

    _logger.warning("Could not find view arch definition in file '%s' for xmlid '%s'", filepath, xmlid)
    return None