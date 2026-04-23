def _get_uri(uri, reference, base_uri=""):
    """
    Returns the content within `reference` that is identified by `uri`.
    Canonicalization is used to convert node reference to an octet stream.
    - URIs starting with # are same-document references
    https://www.w3.org/TR/xmldsig-core/#sec-URI
    - Empty URIs point to the whole document tree, without the signature
    https://www.w3.org/TR/xmldsig-core/#sec-EnvelopedSignature
    Returns an UTF-8 encoded bytes string.
    """
    node = deepcopy(reference.getroottree().getroot())
    if uri == base_uri:
        # Base URI: whole document, without signature (default is empty URI)
        for signature in node.xpath('ds:Signature', namespaces=NS_MAP):
            if signature.tail:
                # move the tail to the previous node or to the parent
                if (previous := signature.getprevious()) is not None:
                    previous.tail = "".join([previous.tail or "", signature.tail or ""])
                else:
                    signature.getparent().text = "".join([signature.getparent().text or "", signature.tail or ""])
            node.remove(signature)
        return _canonicalize_node(node)

    if uri.startswith("#"):
        path = "//*[@*[local-name() = '{}' ]=$uri]"
        results = node.xpath(path.format("Id"), uri=uri.lstrip("#"))  # case-sensitive 'Id'
        if len(results) == 1:
            return _canonicalize_node(results[0])
        if len(results) > 1:
            raise UserError(f"Ambiguous reference URI {uri} resolved to {len(results)} nodes")  # pylint: disable=missing-gettext

    raise UserError(f'URI {uri} not found')