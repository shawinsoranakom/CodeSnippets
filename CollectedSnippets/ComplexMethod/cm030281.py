def ToUnicode(label):
    if len(label) > 1024:
        # Protection from https://github.com/python/cpython/issues/98433.
        # https://datatracker.ietf.org/doc/html/rfc5894#section-6
        # doesn't specify a label size limit prior to NAMEPREP. But having
        # one makes practical sense.
        # This leaves ample room for nameprep() to remove Nothing characters
        # per https://www.rfc-editor.org/rfc/rfc3454#section-3.1 while still
        # preventing us from wasting time decoding a big thing that'll just
        # hit the actual <= 63 length limit in Step 6.
        if isinstance(label, str):
            label = label.encode("utf-8", errors="backslashreplace")
        raise UnicodeDecodeError("idna", label, 0, len(label), "label way too long")
    # Step 1: Check for ASCII
    if isinstance(label, bytes):
        pure_ascii = True
    else:
        try:
            label = label.encode("ascii")
            pure_ascii = True
        except UnicodeEncodeError:
            pure_ascii = False
    if not pure_ascii:
        assert isinstance(label, str)
        # Step 2: Perform nameprep
        label = nameprep(label)
        # It doesn't say this, but apparently, it should be ASCII now
        try:
            label = label.encode("ascii")
        except UnicodeEncodeError as exc:
            raise UnicodeEncodeError("idna", label, exc.start, exc.end,
                                     "Invalid character in IDN label")
    # Step 3: Check for ACE prefix
    assert isinstance(label, bytes)
    if not label.lower().startswith(ace_prefix):
        return str(label, "ascii")

    # Step 4: Remove ACE prefix
    label1 = label[len(ace_prefix):]

    # Step 5: Decode using PUNYCODE
    try:
        result = label1.decode("punycode")
    except UnicodeDecodeError as exc:
        offset = len(ace_prefix)
        raise UnicodeDecodeError("idna", label, offset+exc.start, offset+exc.end, exc.reason)

    # Step 6: Apply ToASCII
    label2 = ToASCII(result)

    # Step 7: Compare the result of step 6 with the one of step 3
    # label2 will already be in lower case.
    if str(label, "ascii").lower() != str(label2, "ascii"):
        raise UnicodeDecodeError("idna", label, 0, len(label),
                                 f"IDNA does not round-trip, '{label!r}' != '{label2!r}'")

    # Step 8: return the result of step 5
    return result