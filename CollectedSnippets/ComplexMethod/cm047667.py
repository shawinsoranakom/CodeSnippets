def _extract_translatable_qweb_terms(element, callback):
    """ Helper method to walk an etree document representing
        a QWeb template, and call ``callback(term)`` for each
        translatable term that is found in the document.

        :param etree._Element element: root of etree document to extract terms from
        :param Callable callback: a callable in the form ``f(term, source_line)``,
                                  that will be called for each extracted term.
    """
    # not using elementTree.iterparse because we need to skip sub-trees in case
    # the ancestor element had a reason to be skipped
    for el in element:
        if isinstance(el, SKIPPED_ELEMENT_TYPES): continue
        if (el.tag.lower() not in SKIPPED_ELEMENTS
                and "t-js" not in el.attrib
                and not (el.tag == 'attribute' and not is_translatable_attrib(el.get('name'), el))
                and el.get("t-translation", '').strip() != "off"):

            _push(callback, el.text, el.sourceline)
            # heuristic: tags with names starting with an uppercase letter are
            # component nodes
            is_component = el.tag[0].isupper() or "t-component" in el.attrib or "t-set-slot" in el.attrib
            for attr in el.attrib:
                if (not is_component and attr in OWL_TRANSLATED_ATTRS) or (is_component and attr.endswith(".translate")):
                    _push(callback, el.attrib[attr], el.sourceline)
            _extract_translatable_qweb_terms(el, callback)
        _push(callback, el.tail, el.sourceline)