def apply_key(key, obj, is_last):
        branching = False

        if obj is None and _traverse_string:
            if key is Ellipsis or callable(key) or isinstance(key, slice):
                branching = True
                result = ()
            else:
                result = None

        elif key is None:
            result = obj

        elif isinstance(key, set):
            assert len(key) >= 1, 'At least one item is required in a `set` key'
            if all(isinstance(item, type) for item in key):
                result = obj if isinstance(obj, tuple(key)) else None
            else:
                item = next(iter(key))
                assert len(key) == 1, 'Multiple items in a `set` key must all be types'
                result = try_call(item, args=(obj,)) if not isinstance(item, type) else None

        elif isinstance(key, (list, tuple)):
            branching = True
            result = from_iterable(
                apply_path(obj, branch, is_last)[0] for branch in key)

        elif key is Ellipsis:
            branching = True
            if isinstance(obj, compat_http_cookies.Morsel):
                obj = dict(obj, key=obj.key, value=obj.value)
            if isinstance(obj, compat_collections_abc.Mapping):
                result = obj.values()
            elif is_iterable_like(obj, (compat_collections_abc.Iterable, compat_etree_Element)):
                result = obj
            elif isinstance(obj, compat_re_Match):
                result = obj.groups()
            elif _traverse_string:
                branching = False
                result = str(obj)
            else:
                result = ()

        elif callable(key):
            branching = True
            if isinstance(obj, compat_http_cookies.Morsel):
                obj = dict(obj, key=obj.key, value=obj.value)
            if isinstance(obj, compat_collections_abc.Mapping):
                iter_obj = obj.items()
            elif is_iterable_like(obj, (compat_collections_abc.Iterable, compat_etree_Element)):
                iter_obj = enumerate(obj)
            elif isinstance(obj, compat_re_Match):
                iter_obj = itertools.chain(
                    enumerate(itertools.chain((obj.group(),), obj.groups())),
                    obj.groupdict().items())
            elif _traverse_string:
                branching = False
                iter_obj = enumerate(str(obj))
            else:
                iter_obj = ()

            result = (v for k, v in iter_obj if try_call(key, args=(k, v)))
            if not branching:  # string traversal
                result = ''.join(result)

        elif isinstance(key, dict_):
            iter_obj = ((k, _traverse_obj(obj, v, False, is_last)) for k, v in key.items())
            result = dict((k, v if v is not None else default) for k, v in iter_obj
                          if v is not None or default is not NO_DEFAULT) or None

        elif isinstance(obj, compat_collections_abc.Mapping):
            if isinstance(obj, compat_http_cookies.Morsel):
                obj = dict(obj, key=obj.key, value=obj.value)
            result = (try_call(obj.get, args=(key,))
                      if casesense or try_call(obj.__contains__, args=(key,))
                      else next((v for k, v in obj.items() if casefold(k) == key), None))

        elif isinstance(obj, compat_re_Match):
            result = None
            if isinstance(key, int) or casesense:
                # Py 2.6 doesn't have methods in the Match class/type
                result = lookup_or_none(obj, key, getter=lambda _, k: obj.group(k))

            elif isinstance(key, str):
                result = next((v for k, v in obj.groupdict().items()
                              if casefold(k) == key), None)

        else:
            result = None
            if isinstance(key, (int, slice)):
                if is_iterable_like(obj, (compat_collections_abc.Sequence, compat_etree_Element)):
                    branching = isinstance(key, slice)
                    result = lookup_or_none(obj, key)
                elif _traverse_string:
                    result = lookup_or_none(str(obj), key)

            elif isinstance(obj, compat_etree_Element) and isinstance(key, str):
                xpath, _, special = key.rpartition('/')
                if not special.startswith('@') and not special.endswith('()'):
                    xpath = key
                    special = None

                # Allow abbreviations of relative paths, absolute paths error
                if xpath.startswith('/'):
                    xpath = '.' + xpath
                elif xpath and not xpath.startswith('./'):
                    xpath = './' + xpath

                def apply_specials(element):
                    if special is None:
                        return element
                    if special == '@':
                        return element.attrib
                    if special.startswith('@'):
                        return try_call(element.attrib.get, args=(special[1:],))
                    if special == 'text()':
                        return element.text
                    raise SyntaxError('apply_specials is missing case for {0!r}'.format(special))

                if xpath:
                    result = list(map(apply_specials, compat_etree_iterfind(obj, xpath)))
                else:
                    result = apply_specials(obj)

        return branching, result if branching else (result,)