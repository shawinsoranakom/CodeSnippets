def _check_with_xsd(tree_or_str, stream, env=None, prefix=None):
    """Check an XML against an XSD schema.

    This will raise a UserError if the XML file is not valid according to the
    XSD file.

    :param str | etree._Element tree_or_str: representation of the tree to be checked
    :param io.IOBase | str stream: the byte stream used to build the XSD schema.
        If env is given, it can also be the name of an attachment in the filestore
    :param odoo.api.Environment env: If it is given, it enables resolving the
        imports of the schema in the filestore with ir.attachments.
    :param str prefix: if given, provides a prefix to try when
        resolving the imports of the schema. e.g. prefix='l10n_cl_edi' will
        enable 'SiiTypes_v10.xsd' to be resolved to 'l10n_cl_edi.SiiTypes_v10.xsd'.
    """
    if not isinstance(tree_or_str, etree._Element):
        tree_or_str = etree.fromstring(tree_or_str)
    parser = etree.XMLParser()
    if env:
        parser.resolvers.add(odoo_resolver(env, prefix))
        if isinstance(stream, str) and stream.endswith('.xsd'):
            attachment = env['ir.attachment'].search([('name', '=', stream)])
            if not attachment:
                raise FileNotFoundError()
            stream = BytesIO(attachment.raw)
    xsd_schema = etree.XMLSchema(etree.parse(stream, parser=parser))
    try:
        xsd_schema.assertValid(tree_or_str)
    except etree.DocumentInvalid as xml_errors:
        raise UserError('\n'.join(str(e) for e in xml_errors.error_log))