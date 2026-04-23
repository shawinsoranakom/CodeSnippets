def xmliter(obj: Response | str | bytes, nodename: str) -> Iterator[Selector]:
    """Return a iterator of Selector's over all nodes of a XML document,
       given the name of the node to iterate. Useful for parsing XML feeds.

    obj can be:
    - a Response object
    - a unicode string
    - a string encoded as utf-8
    """
    warn(
        (
            "xmliter is deprecated and its use strongly discouraged because "
            "it is vulnerable to ReDoS attacks. Use xmliter_lxml instead. See "
            "https://github.com/scrapy/scrapy/security/advisories/GHSA-cc65-xxvf-f7r9"
        ),
        ScrapyDeprecationWarning,
        stacklevel=2,
    )

    nodename_patt = re.escape(nodename)

    DOCUMENT_HEADER_RE = re.compile(r"<\?xml[^>]+>\s*", re.DOTALL)
    HEADER_END_RE = re.compile(rf"<\s*/{nodename_patt}\s*>", re.DOTALL)
    END_TAG_RE = re.compile(r"<\s*/([^\s>]+)\s*>", re.DOTALL)
    NAMESPACE_RE = re.compile(r"((xmlns[:A-Za-z]*)=[^>\s]+)", re.DOTALL)
    text = _body_or_str(obj)

    document_header_match = re.search(DOCUMENT_HEADER_RE, text)
    document_header = (
        document_header_match.group().strip() if document_header_match else ""
    )
    header_end_idx = re_rsearch(HEADER_END_RE, text)
    header_end = text[header_end_idx[1] :].strip() if header_end_idx else ""
    namespaces: dict[str, str] = {}
    if header_end:
        for tagname in reversed(re.findall(END_TAG_RE, header_end)):
            assert header_end_idx
            tag = re.search(
                rf"<\s*{tagname}.*?xmlns[:=][^>]*>",
                text[: header_end_idx[1]],
                re.DOTALL,
            )
            if tag:
                for x in re.findall(NAMESPACE_RE, tag.group()):
                    namespaces[x[1]] = x[0]

    r = re.compile(rf"<{nodename_patt}[\s>].*?</{nodename_patt}>", re.DOTALL)
    for match in r.finditer(text):
        nodetext = (
            document_header
            + match.group().replace(
                nodename, f"{nodename} {' '.join(namespaces.values())}", 1
            )
            + header_end
        )
        yield Selector(text=nodetext, type="xml")