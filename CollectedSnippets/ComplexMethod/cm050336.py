def remove_signature_fallback(content):
    """ The invoice content is inside an ASN1 node identified by PKCS7_DATA_OID (pkcs7-data).
        The node is defined as an OctectString, which can be composed of an arbitrary
        sequence of octects of string data.
        We visit in-order the ASN1 tree nodes until we find the pkcs7-data, then we look for content.
        Once we found it, we read all OctectString that get yielded by the in-order visit..
        When there are no more OctectStrings, then another object will follow
        with its header and identifier, so we stop exploring and just return the content.

        See also:
        https://datatracker.ietf.org/doc/html/rfc2315
        https://www.oss.com/asn1/resources/asn1-made-simple/asn1-quick-reference/octetstring.html
    """
    PKCS7_DATA_OID = '1.2.840.113549.1.7.1'
    result, header_found, data_found = None, False, False
    for node in Reader().build_from_stream(content):
        if node.kind == 'ObjectIdentifier' and node.content == PKCS7_DATA_OID:
            header_found = True
        if header_found and node.kind == 'OctetString':
            data_found = True
            result = (result or b'') + node.content
        elif data_found:
            break

    if not header_found:
        raise Exception("ASN1 Header not found")
    if not data_found:
        raise Exception("ASN1 Content not found")
    return result