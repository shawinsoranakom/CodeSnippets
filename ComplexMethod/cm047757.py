def html2plaintext(
    html: str | markupsafe.Markup | Literal[False] | None,
    body_id: str | None = None,
    encoding: str = 'utf-8',
    include_references: bool = True
) -> str:
    """ From an HTML text, convert the HTML to plain text.
    If @param body_id is provided then this is the tag where the
    body (not necessarily <body>) starts.
    :param include_references: If False, numbered references and
        URLs for links and images will not be included.
    """
    ## (c) Fry-IT, www.fry-it.com, 2007
    ## <peter@fry-it.com>
    ## download here: http://www.peterbe.com/plog/html2plaintext
    if not (html and html.strip()):
        return ''

    if isinstance(html, bytes):
        html = html.decode(encoding)
    else:
        assert isinstance(html, str), f"expected str got {html.__class__.__name__}"

    tree = etree.fromstring(html, parser=etree.HTMLParser())

    if body_id is not None:
        source = tree.xpath('//*[@id=%s]' % (body_id,))
    else:
        source = tree.xpath('//body')
    if len(source):
        tree = source[0]

    url_index = []
    linkrefs = itertools.count(1)
    if include_references:
        for link in tree.findall('.//a'):
            if url := link.get('href'):
                link.tag = 'span'
                link.text = f'{link.text} [{next(linkrefs)}]'
                url_index.append(url)

        for img in tree.findall('.//img'):
            if src := img.get('src'):
                img.tag = 'span'
                if src.startswith('data:'):
                    img_name = None  # base64 image
                else:
                    img_name = re.search(r'[^/]+(?=\.[a-zA-Z]+(?:\?|$))', src)
                img.text = '%s [%s]' % (img_name[0] if img_name else 'Image', next(linkrefs))
                url_index.append(src)

    html = etree.tostring(tree, encoding="unicode")
    # \r char is converted into &#13;, must remove it
    html = html.replace('&#13;', '')

    html = html.replace('<strong>', '*').replace('</strong>', '*')
    html = html.replace('<b>', '*').replace('</b>', '*')
    html = html.replace('<h3>', '*').replace('</h3>', '*')
    html = html.replace('<h2>', '**').replace('</h2>', '**')
    html = html.replace('<h1>', '**').replace('</h1>', '**')
    html = html.replace('<em>', '/').replace('</em>', '/')
    html = html.replace('<tr>', '\n')
    html = html.replace('</p>', '\n')
    html = re.sub(r'<br\s*/?>', '\n', html)
    html = re.sub('<.*?>', ' ', html)
    html = html.replace(' ' * 2, ' ')
    html = html.replace('&gt;', '>')
    html = html.replace('&lt;', '<')
    html = html.replace('&amp;', '&')
    html = html.replace('&nbsp;', '\N{NO-BREAK SPACE}')

    # strip all lines
    html = '\n'.join([x.strip() for x in html.splitlines()])
    html = html.replace('\n' * 2, '\n')

    if url_index:
        html += '\n\n'
        for i, url in enumerate(url_index, start=1):
            html += f'[{i}] {url}\n'

    return html.strip()