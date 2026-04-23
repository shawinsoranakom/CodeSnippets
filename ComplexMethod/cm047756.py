def html_normalize(src, filter_callback=None, output_method="html"):
    """ Normalize `src` for storage as an html field value.

    The string is parsed as an html tag soup, made valid, then decorated for
    "email quote" detection, and prepared for an optional filtering.
    The filtering step (e.g. sanitization) should be performed by the
    `filter_callback` function (to avoid multiple parsing operations, and
    normalize the result).

    :param src: the html string to normalize
    :param filter_callback: optional callable taking a single `etree._Element`
        document parameter, to be called during normalization in order to
        filter the output document
    :param output_method: defines the output method to pass to `html.tostring`.
        It defaults to 'html', but can also be 'xml' for xhtml output.
    """
    if not src:
        return src

    # html: remove encoding attribute inside tags
    src = re.sub(r'(<[^>]*\s)(encoding=(["\'][^"\']*?["\']|[^\s\n\r>]+)(\s[^>]*|/)?>)', "", src)

    src = src.replace('--!>', '-->')
    src = re.sub(r'(<!-->|<!--->)', '<!-- -->', src)
    # On the specific case of Outlook desktop it adds unnecessary '<o:.*></o:.*>' tags which are parsed
    # in '<p></p>' which may alter the appearance (eg. spacing) of the mail body
    src = re.sub(r'</?o:.*?>', '', src)

    try:
        doc, single_body_element = fromstring(src)
    except etree.ParserError as e:
        # HTML comment only string, whitespace only..
        if 'empty' in str(e):
            return ""
        raise

    # perform quote detection before cleaning and class removal
    for el in doc.iter(tag=etree.Element):
        tag_quote(el)

    doc = html.fromstring(html.tostring(doc, method=output_method))

    if filter_callback:
        doc = filter_callback(doc)

    src = html.tostring(doc, encoding='unicode', method=output_method)

    if not single_body_element and src.startswith('<div>') and src.endswith('</div>'):
        # the <div></div> may come from 2 places
        # 1. the src is parsed as multiple body elements
        #    <div></div> wraps all elements.
        # 2. the src is parsed as not only body elements
        #    <html></html> wraps all elements.
        #    then the Cleaner as the filter_callback which has 'html' in its
        #    'remove_tags' will write <html></html> to <div></div> since it
        #    cannot directly drop the parent-most tag
        src = src[5:-6]

    # html considerations so real html content match database value
    src = src.replace(u'\xa0', u'&nbsp;')

    return src