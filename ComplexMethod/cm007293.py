def xpath_element(node, xpath, name=None, fatal=False, default=NO_DEFAULT):
    def _find_xpath(xpath):
        return node.find(compat_xpath(xpath))

    if isinstance(xpath, compat_basestring):
        n = _find_xpath(xpath)
    else:
        for xp in xpath:
            n = _find_xpath(xp)
            if n is not None:
                break

    if n is None:
        if default is not NO_DEFAULT:
            return default
        elif fatal:
            name = xpath if name is None else name
            raise ExtractorError('Could not find XML element %s' % name)
        else:
            return None
    return n