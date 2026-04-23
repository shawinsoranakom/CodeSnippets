def fromstring(html_, base_url=None, parser=None, **kw):
    """
    This function mimics lxml.html.fromstring. It not only returns the parsed
    element/document but also a flag indicating whether the input is for a
    a single body element or not.

    This tries to minimally parse the chunk of text, without knowing if it
    is a fragment or a document.

    base_url will set the document's base_url attribute (and the tree's docinfo.URL)
    """
    if parser is None:
        parser = html_parser
    if isinstance(html_, bytes):
        is_full_html = _looks_like_full_html_bytes(html_)
    else:
        is_full_html = _looks_like_full_html_unicode(html_)
    doc = document_fromstring(html_, parser=parser, base_url=base_url, **kw)
    if is_full_html:
        return doc, False
    # otherwise, lets parse it out...
    bodies = doc.findall('body')
    if not bodies:
        bodies = doc.findall('{%s}body' % XHTML_NAMESPACE)
    if bodies:
        body = bodies[0]
        if len(bodies) > 1:
            # Somehow there are multiple bodies, which is bad, but just
            # smash them into one body
            for other_body in bodies[1:]:
                if other_body.text:
                    if len(body):
                        body[-1].tail = (body[-1].tail or '') + other_body.text
                    else:
                        body.text = (body.text or '') + other_body.text
                body.extend(other_body)
                # We'll ignore tail
                # I guess we are ignoring attributes too
                other_body.drop_tree()
    else:
        body = None
    heads = doc.findall('head')
    if not heads:
        heads = doc.findall('{%s}head' % XHTML_NAMESPACE)
    if heads:
        # Well, we have some sort of structure, so lets keep it all
        head = heads[0]
        if len(heads) > 1:
            for other_head in heads[1:]:
                head.extend(other_head)
                # We don't care about text or tail in a head
                other_head.drop_tree()
        return doc, False
    if body is None:
        return doc, False
    if (len(body) == 1 and (not body.text or not body.text.strip())
        and (not body[-1].tail or not body[-1].tail.strip())):
        # The body has just one element, so it was probably a single
        # element passed in
        return body[0], True
    # Now we have a body which represents a bunch of tags which have the
    # content that was passed in.  We will create a fake container, which
    # is the body tag, except <body> implies too much structure.
    if _contains_block_level_tag(body):
        body.tag = 'div'
    else:
        body.tag = 'span'
    return body, False