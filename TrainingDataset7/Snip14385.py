def uri_to_iri(uri):
    """
    Convert a Uniform Resource Identifier(URI) into an Internationalized
    Resource Identifier(IRI).

    This is the algorithm from RFC 3987 Section 3.2, excluding step 4.

    Take an URI in ASCII bytes (e.g. '/I%20%E2%99%A5%20Django/') and return
    a string containing the encoded result (e.g. '/I%20♥%20Django/').
    """
    if uri is None:
        return uri
    uri = force_bytes(uri)
    # Fast selective unquote: First, split on '%' and then starting with the
    # second block, decode the first 2 bytes if they represent a hex code to
    # decode. The rest of the block is the part after '%AB', not containing
    # any '%'. Add that to the output without further processing.
    bits = uri.split(b"%")
    if len(bits) == 1:
        iri = uri
    else:
        parts = [bits[0]]
        append = parts.append
        hextobyte = _hextobyte
        for item in bits[1:]:
            hex = item[:2]
            if hex in hextobyte:
                append(hextobyte[item[:2]])
                append(item[2:])
            else:
                append(b"%")
                append(item)
        iri = b"".join(parts)
    return repercent_broken_unicode(iri).decode()