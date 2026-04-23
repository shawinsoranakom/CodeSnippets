def decode_header(header):
    """Decode a message header value without converting charset.

    For historical reasons, this function may return either:

    1. A list of length 1 containing a pair (str, None).
    2. A list of (bytes, charset) pairs containing each of the decoded
       parts of the header.  Charset is None for non-encoded parts of the header,
       otherwise a lower-case string containing the name of the character set
       specified in the encoded string.

    header may be a string that may or may not contain RFC2047 encoded words,
    or it may be a Header object.

    An email.errors.HeaderParseError may be raised when certain decoding error
    occurs (e.g. a base64 decoding exception).

    This function exists for backwards compatibility only. For new code, we
    recommend using email.headerregistry.HeaderRegistry instead.
    """
    # If it is a Header object, we can just return the encoded chunks.
    if hasattr(header, '_chunks'):
        return [(_charset._encode(string, str(charset)), str(charset))
                    for string, charset in header._chunks]
    # If no encoding, just return the header with no charset.
    if not ecre.search(header):
        return [(header, None)]
    # First step is to parse all the encoded parts into triplets of the form
    # (encoded_string, encoding, charset).  For unencoded strings, the last
    # two parts will be None.
    words = []
    for line in header.splitlines():
        parts = ecre.split(line)
        first = True
        while parts:
            unencoded = parts.pop(0)
            if first:
                unencoded = unencoded.lstrip()
                first = False
            if unencoded:
                words.append((unencoded, None, None))
            if parts:
                charset = parts.pop(0).lower()
                encoding = parts.pop(0).lower()
                encoded = parts.pop(0)
                words.append((encoded, encoding, charset))
    # Now loop over words and remove words that consist of whitespace
    # between two encoded strings.
    droplist = []
    for n, w in enumerate(words):
        if n>1 and w[1] and words[n-2][1] and words[n-1][0].isspace():
            droplist.append(n-1)
    for d in reversed(droplist):
        del words[d]

    # The next step is to decode each encoded word by applying the reverse
    # base64 or quopri transformation.  decoded_words is now a list of the
    # form (decoded_word, charset).
    decoded_words = []
    for encoded_string, encoding, charset in words:
        if encoding is None:
            # This is an unencoded word.
            decoded_words.append((encoded_string, charset))
        elif encoding == 'q':
            word = email.quoprimime.header_decode(encoded_string)
            decoded_words.append((word, charset))
        elif encoding == 'b':
            paderr = len(encoded_string) % 4   # Postel's law: add missing padding
            if paderr:
                encoded_string += '==='[:4 - paderr]
            try:
                word = email.base64mime.decode(encoded_string)
            except binascii.Error:
                raise HeaderParseError('Base64 decoding error')
            else:
                decoded_words.append((word, charset))
        else:
            raise AssertionError('Unexpected encoding: ' + encoding)
    # Now convert all words to bytes and collapse consecutive runs of
    # similarly encoded words.
    collapsed = []
    last_word = last_charset = None
    for word, charset in decoded_words:
        if isinstance(word, str):
            word = bytes(word, 'raw-unicode-escape')
        if last_word is None:
            last_word = word
            last_charset = charset
        elif charset != last_charset:
            collapsed.append((last_word, last_charset))
            last_word = word
            last_charset = charset
        elif last_charset is None:
            last_word += BSPACE + word
        else:
            last_word += word
    collapsed.append((last_word, last_charset))
    return collapsed