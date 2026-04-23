def _prepare_predicate(next_, token):
        signature = []
        predicate = []
        for token in next_:
            if token[0] == "]":
                break
            if token[0] and token[0][:1] in "'\"":
                token = "'", token[0][1:-1]
            signature.append(token[0] or "-")
            predicate.append(token[1])

        def select(context, result, filter_fn=lambda _: True):
            for elem in result:
                if filter_fn(elem):
                    yield elem

        signature = "".join(signature)
        # use signature to determine predicate type
        if signature == "@-":
            # [@attribute] predicate
            key = predicate[1]
            return functools.partial(
                select, filter_fn=lambda el: el.get(key) is not None)
        if signature == "@-='":
            # [@attribute='value']
            key = predicate[1]
            value = predicate[-1]
            return functools.partial(
                select, filter_fn=lambda el: el.get(key) == value)
        if signature == "-" and not re.match(r"\d+$", predicate[0]):
            # [tag]
            tag = predicate[0]
            return functools.partial(
                select, filter_fn=lambda el: el.find(tag) is not None)
        if signature == "-='" and not re.match(r"\d+$", predicate[0]):
            # [tag='value']
            tag = predicate[0]
            value = predicate[-1]

            def itertext(el):
                for e in el.getiterator():
                    e = e.text
                    if e:
                        yield e

            def select(context, result):
                for elem in result:
                    for e in elem.findall(tag):
                        if "".join(itertext(e)) == value:
                            yield elem
                            break
            return select
        if signature == "-" or signature == "-()" or signature == "-()-":
            # [index] or [last()] or [last()-index]
            if signature == "-":
                index = int(predicate[0]) - 1
            else:
                if predicate[0] != "last":
                    raise SyntaxError("unsupported function")
                if signature == "-()-":
                    try:
                        index = int(predicate[2]) - 1
                    except ValueError:
                        raise SyntaxError("unsupported expression")
                else:
                    index = -1

            def select(context, result):
                parent_map = _get_parent_map(context)
                for elem in result:
                    try:
                        parent = parent_map[elem]
                        # FIXME: what if the selector is "*" ?
                        elems = list(parent.findall(elem.tag))
                        if elems[index] is elem:
                            yield elem
                    except (IndexError, KeyError):
                        pass
            return select
        raise SyntaxError("invalid predicate")