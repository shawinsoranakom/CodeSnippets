def tag_quote(el):
    def _create_new_node(tag, text, tail=None, attrs=None):
        new_node = etree.Element(tag)
        new_node.text = text
        new_node.tail = tail
        if attrs:
            for key, val in attrs.items():
                new_node.set(key, val)
        return new_node

    def _tag_matching_regex_in_text(regex, node, tag='span', attrs=None):
        text = node.text or ''
        if not re.search(regex, text):
            return

        child_node = None
        idx, node_idx = 0, 0
        for item in re.finditer(regex, text):
            new_node = _create_new_node(tag, text[item.start():item.end()], None, attrs)
            if child_node is None:
                node.text = text[idx:item.start()]
                new_node.tail = text[item.end():]
                node.insert(node_idx, new_node)
            else:
                child_node.tail = text[idx:item.start()]
                new_node.tail = text[item.end():]
                node.insert(node_idx, new_node)
            child_node = new_node
            idx = item.end()
            node_idx = node_idx + 1

    el_class = el.get('class', '') or ''
    el_id = el.get('id', '') or ''

    # gmail or yahoo // # outlook, html // # msoffice
    if 'gmail_extra' in el_class or \
            ('SkyDrivePlaceholder' in el_class or 'SkyDrivePlaceholder' in el_class):
        el.set('data-o-mail-quote', '1')
        if el.getparent() is not None:
            el.getparent().set('data-o-mail-quote-container', '1')

    if (el.tag == 'hr' and ('stopSpelling' in el_class or 'stopSpelling' in el_id)) or \
       'yahoo_quoted' in el_class:
        # Quote all elements after this one
        el.set('data-o-mail-quote', '1')
        for sibling in el.itersiblings(preceding=False):
            sibling.set('data-o-mail-quote', '1')

    # odoo, gmail and outlook automatic signature wrapper
    is_signature_wrapper = 'odoo_signature_wrapper' in el_class or 'gmail_signature' in el_class or el_id == "Signature"
    is_outlook_auto_message = 'appendonsend' in el_id
    # gmail and outlook reply quote
    is_outlook_reply_quote = 'divRplyFwdMsg' in el_id
    is_gmail_quote = 'gmail_quote' in el_class
    is_quote_wrapper = is_signature_wrapper or is_gmail_quote or is_outlook_reply_quote
    if is_quote_wrapper:
        el.set('data-o-mail-quote-container', '1')
        el.set('data-o-mail-quote', '1')

    # outlook reply wrapper is preceded with <hr> and a div containing recipient info
    if is_outlook_reply_quote:
        hr = el.getprevious()
        reply_quote = el.getnext()
        if hr is not None and hr.tag == 'hr':
            hr.set('data-o-mail-quote', '1')
        if reply_quote is not None:
            reply_quote.set('data-o-mail-quote-container', '1')
            reply_quote.set('data-o-mail-quote', '1')

    if is_outlook_auto_message:
        if not el.text or not el.text.strip():
            el.set('data-o-mail-quote-container', '1')
            el.set('data-o-mail-quote', '1')

    # html signature (-- <br />blah)
    signature_begin = re.compile(r"((?:(?:^|\n)[-]{2}[\s]?$))")
    if el.text and el.find('br') is not None and re.search(signature_begin, el.text):
        el.set('data-o-mail-quote', '1')
        if el.getparent() is not None:
            el.getparent().set('data-o-mail-quote-container', '1')

    # text-based quotes (>, >>) and signatures (-- Signature)
    text_complete_regex = re.compile(r"((?:\n[>]+[^\n\r]*)+|(?:(?:^|\n)[-]{2}[\s]?[\r\n]{1,2}[\s\S]+))")
    if not el.get('data-o-mail-quote'):
        _tag_matching_regex_in_text(text_complete_regex, el, 'span', {'data-o-mail-quote': '1'})

    if el.tag == 'blockquote':
        # remove single node
        el.set('data-o-mail-quote-node', '1')
        el.set('data-o-mail-quote', '1')
    if el.getparent() is not None and not el.getparent().get('data-o-mail-quote-node'):
        if el.getparent().get('data-o-mail-quote'):
            el.set('data-o-mail-quote', '1')
        # only quoting the elements following the first quote in the container
        # avoids issues with repeated calls to html_normalize
        elif el.getparent().get('data-o-mail-quote-container'):
            if (first_sibling_quote := el.getparent().find("*[@data-o-mail-quote]")) is not None:
                siblings = el.getparent().getchildren()
                quote_index = siblings.index(first_sibling_quote)
                element_index = siblings.index(el)
                if quote_index < element_index:
                    el.set('data-o-mail-quote', '1')
    if el.getprevious() is not None and el.getprevious().get('data-o-mail-quote') and not el.text_content().strip():
        el.set('data-o-mail-quote', '1')