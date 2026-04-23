def ToASCII(label):  # type: (str) -> bytes
    try:
        # Step 1: try ASCII
        label_ascii = label.encode("ascii")
    except UnicodeEncodeError:
        pass
    else:
        # Skip to step 3: UseSTD3ASCIIRules is false, so
        # Skip to step 8.
        if 0 < len(label_ascii) < 64:
            return label_ascii
        if len(label) == 0:
            raise UnicodeEncodeError("idna", label, 0, 1, "label empty")
        else:
            raise UnicodeEncodeError("idna", label, 0, len(label), "label too long")

    # Step 2: nameprep
    label = nameprep(label)

    # Step 3: UseSTD3ASCIIRules is false
    # Step 4: try ASCII
    try:
        label_ascii = label.encode("ascii")
    except UnicodeEncodeError:
        pass
    else:
        # Skip to step 8.
        if 0 < len(label) < 64:
            return label_ascii
        if len(label) == 0:
            raise UnicodeEncodeError("idna", label, 0, 1, "label empty")
        else:
            raise UnicodeEncodeError("idna", label, 0, len(label), "label too long")

    # Step 5: Check ACE prefix
    if label.lower().startswith(sace_prefix):
        raise UnicodeEncodeError(
            "idna", label, 0, len(sace_prefix), "Label starts with ACE prefix")

    # Step 6: Encode with PUNYCODE
    label_ascii = label.encode("punycode")

    # Step 7: Prepend ACE prefix
    label_ascii = ace_prefix + label_ascii

    # Step 8: Check size
    # do not check for empty as we prepend ace_prefix.
    if len(label_ascii) < 64:
        return label_ascii
    raise UnicodeEncodeError("idna", label, 0, len(label), "label too long")