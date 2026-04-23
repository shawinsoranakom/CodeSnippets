def split_header_words(header_values):
    r"""Parse header values into a list of lists containing key,value pairs.

    The function knows how to deal with ",", ";" and "=" as well as quoted
    values after "=".  A list of space separated tokens are parsed as if they
    were separated by ";".

    If the header_values passed as argument contains multiple values, then they
    are treated as if they were a single value separated by comma ",".

    This means that this function is useful for parsing header fields that
    follow this syntax (BNF as from the HTTP/1.1 specification, but we relax
    the requirement for tokens).

      headers           = #header
      header            = (token | parameter) *( [";"] (token | parameter))

      token             = 1*<any CHAR except CTLs or separators>
      separators        = "(" | ")" | "<" | ">" | "@"
                        | "," | ";" | ":" | "\" | <">
                        | "/" | "[" | "]" | "?" | "="
                        | "{" | "}" | SP | HT

      quoted-string     = ( <"> *(qdtext | quoted-pair ) <"> )
      qdtext            = <any TEXT except <">>
      quoted-pair       = "\" CHAR

      parameter         = attribute "=" value
      attribute         = token
      value             = token | quoted-string

    Each header is represented by a list of key/value pairs.  The value for a
    simple token (not part of a parameter) is None.  Syntactically incorrect
    headers will not necessarily be parsed as you would want.

    This is easier to describe with some examples:

    >>> split_header_words(['foo="bar"; port="80,81"; discard, bar=baz'])
    [[('foo', 'bar'), ('port', '80,81'), ('discard', None)], [('bar', 'baz')]]
    >>> split_header_words(['text/html; charset="iso-8859-1"'])
    [[('text/html', None), ('charset', 'iso-8859-1')]]
    >>> split_header_words([r'Basic realm="\"foo\bar\""'])
    [[('Basic', None), ('realm', '"foobar"')]]

    """
    assert not isinstance(header_values, str)
    result = []
    for text in header_values:
        orig_text = text
        pairs = []
        while text:
            m = HEADER_TOKEN_RE.search(text)
            if m:
                text = unmatched(m)
                name = m.group(1)
                m = HEADER_QUOTED_VALUE_RE.search(text)
                if m:  # quoted value
                    text = unmatched(m)
                    value = m.group(1)
                    value = HEADER_ESCAPE_RE.sub(r"\1", value)
                else:
                    m = HEADER_VALUE_RE.search(text)
                    if m:  # unquoted value
                        text = unmatched(m)
                        value = m.group(1)
                        value = value.rstrip()
                    else:
                        # no value, a lone token
                        value = None
                pairs.append((name, value))
            elif text.lstrip().startswith(","):
                # concatenated headers, as per RFC 2616 section 4.2
                text = text.lstrip()[1:]
                if pairs: result.append(pairs)
                pairs = []
            else:
                # skip junk
                non_junk, nr_junk_chars = re.subn(r"^[=\s;]*", "", text)
                assert nr_junk_chars > 0, (
                    "split_header_words bug: '%s', '%s', %s" %
                    (orig_text, text, pairs))
                text = non_junk
        if pairs: result.append(pairs)
    return result