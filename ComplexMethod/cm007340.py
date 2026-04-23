def compat_etree_iterfind(elem, path, namespaces=None):
        # compile selector pattern
        if path[-1:] == "/":
            path = path + "*"  # implicit all (FIXME: keep this?)
        try:
            selector = _cache[path]
        except KeyError:
            if len(_cache) > 100:
                _cache.clear()
            if path[:1] == "/":
                raise SyntaxError("cannot use absolute path on element")
            tokens = _xpath_tokenizer(path, namespaces)
            selector = []
            for token in tokens:
                if token[0] == "/":
                    continue
                try:
                    selector.append(ops[token[0]](tokens, token))
                except StopIteration:
                    raise SyntaxError("invalid path")
            _cache[path] = selector
        # execute selector pattern
        result = [elem]
        context = _SelectorContext(elem)
        for select in selector:
            result = select(context, result)
        return result