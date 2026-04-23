def apply_key(key, obj, is_last):
        branching = False
        result = None

        if obj is None and traverse_string:
            if key is ... or callable(key) or isinstance(key, slice):
                branching = True
                result = ()

        elif key is None:
            result = obj

        elif isinstance(key, set):
            item = next(iter(key))
            if len(key) > 1 or isinstance(item, type):
                assert all(isinstance(item, type) for item in key)
                if isinstance(obj, tuple(key)):
                    result = obj
            else:
                result = try_call(item, args=(obj,))

        elif isinstance(key, (list, tuple)):
            branching = True
            result = itertools.chain.from_iterable(
                apply_path(obj, branch, is_last)[0] for branch in key)

        elif key is ...:
            branching = True
            if isinstance(obj, http.cookies.Morsel):
                obj = dict(obj, key=obj.key, value=obj.value)
            if isinstance(obj, collections.abc.Mapping):
                result = obj.values()
            elif is_iterable_like(obj) or isinstance(obj, xml.etree.ElementTree.Element):
                result = obj
            elif isinstance(obj, re.Match):
                result = obj.groups()
            elif traverse_string:
                branching = False
                result = str(obj)
            else:
                result = ()

        elif callable(key):
            branching = True
            if isinstance(obj, http.cookies.Morsel):
                obj = dict(obj, key=obj.key, value=obj.value)
            if isinstance(obj, collections.abc.Mapping):
                iter_obj = obj.items()
            elif is_iterable_like(obj) or isinstance(obj, xml.etree.ElementTree.Element):
                iter_obj = enumerate(obj)
            elif isinstance(obj, re.Match):
                iter_obj = itertools.chain(
                    enumerate((obj.group(), *obj.groups())),
                    obj.groupdict().items())
            elif traverse_string:
                branching = False
                iter_obj = enumerate(str(obj))
            else:
                iter_obj = ()

            result = (v for k, v in iter_obj if try_call(key, args=(k, v)))
            if not branching:  # string traversal
                result = ''.join(result)

        elif isinstance(key, dict):
            iter_obj = ((k, _traverse_obj(obj, v, False, is_last)) for k, v in key.items())
            result = {
                k: v if v is not None else default for k, v in iter_obj
                if v is not None or default is not NO_DEFAULT
            } or None

        elif isinstance(obj, collections.abc.Mapping):
            if isinstance(obj, http.cookies.Morsel):
                obj = dict(obj, key=obj.key, value=obj.value)
            result = (try_call(obj.get, args=(key,)) if casesense or try_call(obj.__contains__, args=(key,)) else
                      next((v for k, v in obj.items() if casefold(k) == key), None))

        elif isinstance(obj, re.Match):
            if isinstance(key, int) or casesense:
                with contextlib.suppress(IndexError):
                    result = obj.group(key)

            elif isinstance(key, str):
                result = next((v for k, v in obj.groupdict().items() if casefold(k) == key), None)

        elif isinstance(key, (int, slice)):
            if is_iterable_like(obj, (collections.abc.Sequence, xml.etree.ElementTree.Element)):
                branching = isinstance(key, slice)
                with contextlib.suppress(IndexError):
                    result = obj[key]
            elif traverse_string:
                with contextlib.suppress(IndexError):
                    result = str(obj)[key]

        elif isinstance(obj, xml.etree.ElementTree.Element) and isinstance(key, str):
            xpath, _, special = key.rpartition('/')
            if not special.startswith('@') and not special.endswith('()'):
                xpath = key
                special = None

            # Allow abbreviations of relative paths, absolute paths error
            if xpath.startswith('/'):
                xpath = f'.{xpath}'
            elif xpath and not xpath.startswith('./'):
                xpath = f'./{xpath}'

            def apply_specials(element):
                if special is None:
                    return element
                if special == '@':
                    return element.attrib
                if special.startswith('@'):
                    return try_call(element.attrib.get, args=(special[1:],))
                if special == 'text()':
                    return element.text
                raise SyntaxError(f'apply_specials is missing case for {special!r}')

            if xpath:
                result = list(map(apply_specials, obj.iterfind(xpath)))
            else:
                result = apply_specials(obj)

        return branching, result if branching else (result,)