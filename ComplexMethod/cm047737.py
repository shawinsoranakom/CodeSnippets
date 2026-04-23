def add_stripped_items_before(node, spec, extract):
    text = spec.text or ''

    before_text = ''
    prev = next((n for n in node.itersiblings(preceding=True) if not (n.tag == etree.ProcessingInstruction and n.target == "apply-inheritance-specs-node-removal")), None)
    if prev is None:
        parent = node.getparent()
        result = parent.text and RSTRIP_REGEXP.search(parent.text)
        before_text = result.group(0) if result else ''
        fallback_text = None if spec.text is None else ''
        parent.text = ((parent.text or '').rstrip() + text) or fallback_text
    else:
        result = prev.tail and RSTRIP_REGEXP.search(prev.tail)
        before_text = result.group(0) if result else ''
        prev.tail = (prev.tail or '').rstrip() + text

    if len(spec) > 0:
        spec[-1].tail = (spec[-1].tail or "").rstrip() + before_text
    else:
        spec.text = (spec.text or "").rstrip() + before_text

    for child in spec:
        if child.get('position') == 'move':
            tail = child.tail
            child = extract(child)
            child.tail = tail
        node.addprevious(child)