def traverse_obj(obj, *paths, **kwargs):
    """
    Safely traverse nested `dict`s and `Iterable`s, etc

    >>> obj = [{}, {"key": "value"}]
    >>> traverse_obj(obj, (1, "key"))
    'value'

    Each of the provided `paths` is tested and the first producing a valid result will be returned.
    The next path will also be tested if the path branched but no results could be found.
    Supported values for traversal are `Mapping`, `Iterable`, `re.Match`, `xml.etree.ElementTree`
    (xpath) and `http.cookies.Morsel`.
    Unhelpful values (`{}`, `None`) are treated as the absence of a value and discarded.

    The paths will be wrapped in `variadic`, so that `'key'` is conveniently the same as `('key', )`.

    The keys in the path can be one of:
        - `None`:           Return the current object.
        - `set`:            Requires the only item in the set to be a type or function,
                            like `{type}`/`{type, type, ...}`/`{func}`. If one or more `type`s,
                            return only values that have one of the types. If a function,
                            return `func(obj)`.
        - `str`/`int`:      Return `obj[key]`. For `re.Match`, return `obj.group(key)`.
        - `slice`:          Branch out and return all values in `obj[key]`.
        - `Ellipsis`:       Branch out and return a list of all values.
        - `tuple`/`list`:   Branch out and return a list of all matching values.
                            Read as: `[traverse_obj(obj, branch) for branch in branches]`.
        - `function`:       Branch out and return values filtered by the function.
                            Read as: `[value for key, value in obj if function(key, value)]`.
                            For `Sequence`s, `key` is the index of the value.
                            For `Iterable`s, `key` is the enumeration count of the value.
                            For `re.Match`es, `key` is the group number (0 = full match)
                            as well as additionally any group names, if given.
        - `dict`:           Transform the current object and return a matching dict.
                            Read as: `{key: traverse_obj(obj, path) for key, path in dct.items()}`.
        - `any`-builtin:    Take the first matching object and return it, resetting branching.
        - `all`-builtin:    Take all matching objects and return them as a list, resetting branching.
        - `filter`-builtin: Return the value if it is truthy, `None` otherwise.

        `tuple`, `list`, and `dict` all support nested paths and branches.

    @params paths           Paths which to traverse by.
    Keyword arguments:
    @param default          Value to return if the paths do not match.
                            If the last key in the path is a `dict`, it will apply to each value inside
                            the dict instead, depth first. Try to avoid if using nested `dict` keys.
    @param expected_type    If a `type`, only accept final values of this type.
                            If any other callable, try to call the function on each result.
                            If the last key in the path is a `dict`, it will apply to each value inside
                            the dict instead, recursively. This does respect branching paths.
    @param get_all          If `False`, return the first matching result, otherwise all matching ones.
    @param casesense        If `False`, consider string dictionary keys as case insensitive.

    The following is only meant to be used by YoutubeDL.prepare_outtmpl and is not part of the API

    @param _traverse_string  Whether to traverse into objects as strings.
                            If `True`, any non-compatible object will first be
                            converted into a string and then traversed into.
                            The return value of that path will be a string instead,
                            not respecting any further branching.


    @returns                The result of the object traversal.
                            If successful, `get_all=True`, and the path branches at least once,
                            then a list of results is returned instead.
                            A list is always returned if the last path branches and no `default` is given.
                            If a path ends on a `dict` that result will always be a `dict`.
    """

    # parameter defaults
    default = kwargs.get('default', NO_DEFAULT)
    expected_type = kwargs.get('expected_type')
    get_all = kwargs.get('get_all', True)
    casesense = kwargs.get('casesense', True)
    _traverse_string = kwargs.get('_traverse_string', False)

    # instant compat
    str = compat_str

    from .compat import (
        compat_builtins_dict as dict_,  # the basic dict type
        compat_dict as dict,            # dict preserving imsertion order
    )

    casefold = lambda k: compat_casefold(k) if isinstance(k, str) else k

    if isinstance(expected_type, type):
        type_test = lambda val: val if isinstance(val, expected_type) else None
    else:
        type_test = lambda val: try_call(expected_type or IDENTITY, args=(val,))

    def lookup_or_none(v, k, getter=None):
        with compat_contextlib_suppress(LookupError):
            return getter(v, k) if getter else v[k]

    def from_iterable(iterables):
        # chain.from_iterable(['ABC', 'DEF']) --> A B C D E F
        for it in iterables:
            for item in it:
                yield item

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

    def lazy_last(iterable):
        iterator = iter(iterable)
        prev = next(iterator, NO_DEFAULT)
        if prev is NO_DEFAULT:
            return

        for item in iterator:
            yield False, prev
            prev = item

        yield True, prev

    def apply_path(start_obj, path, test_type):
        objs = (start_obj,)
        has_branched = False

        key = None
        for last, key in lazy_last(variadic(path, (str, bytes, dict_, set))):
            if not casesense and isinstance(key, str):
                key = compat_casefold(key)

            if key in (any, all):
                has_branched = False
                filtered_objs = (obj for obj in objs if obj not in (None, {}))
                if key is any:
                    objs = (next(filtered_objs, None),)
                else:
                    objs = (list(filtered_objs),)
                continue

            # filter might be from __builtin__, future_builtins, or itertools.ifilter
            if key in compat_filter_fns:
                objs = filter(None, objs)
                continue

            if __debug__ and callable(key):
                # Verify function signature
                _try_bind_args(key, None, None)

            new_objs = []
            for obj in objs:
                branching, results = apply_key(key, obj, last)
                has_branched |= branching
                new_objs.append(results)

            objs = from_iterable(new_objs)

        if test_type and not isinstance(key, (dict_, list, tuple)):
            objs = map(type_test, objs)

        return objs, has_branched, isinstance(key, dict_)

    def _traverse_obj(obj, path, allow_empty, test_type):
        results, has_branched, is_dict = apply_path(obj, path, test_type)
        results = LazyList(x for x in results if x not in (None, {}))

        if get_all and has_branched:
            if results:
                return results.exhaust()
            if allow_empty:
                return [] if default is NO_DEFAULT else default
            return None

        return results[0] if results else {} if allow_empty and is_dict else None

    for index, path in enumerate(paths, 1):
        result = _traverse_obj(obj, path, index == len(paths), True)
        if result is not None:
            return result

    return None if default is NO_DEFAULT else default