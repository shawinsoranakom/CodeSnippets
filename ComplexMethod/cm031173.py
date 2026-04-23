def _escape_attrib(text):
    # escape attribute value
    try:
        if "&" in text:
            text = text.replace("&", "&amp;")
        if "<" in text:
            text = text.replace("<", "&lt;")
        if ">" in text:
            text = text.replace(">", "&gt;")
        if "\"" in text:
            text = text.replace("\"", "&quot;")
        # Although section 2.11 of the XML specification states that CR or
        # CR LN should be replaced with just LN, it applies only to EOLNs
        # which take part of organizing file into lines. Within attributes,
        # we are replacing these with entity numbers, so they do not count.
        # http://www.w3.org/TR/REC-xml/#sec-line-ends
        # The current solution, contained in following six lines, was
        # discussed in issue 17582 and 39011.
        if "\r" in text:
            text = text.replace("\r", "&#13;")
        if "\n" in text:
            text = text.replace("\n", "&#10;")
        if "\t" in text:
            text = text.replace("\t", "&#09;")
        return text
    except (TypeError, AttributeError):
        _raise_serialization_error(text)