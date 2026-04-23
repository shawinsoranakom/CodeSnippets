def _linkcode_resolve(domain, info, package, url_fmt, revision):
    """Determine a link to online source for a class/method/function

    This is called by sphinx.ext.linkcode

    An example with a long-untouched module that everyone has
    >>> _linkcode_resolve('py', {'module': 'tty',
    ...                          'fullname': 'setraw'},
    ...                   package='tty',
    ...                   url_fmt='https://hg.python.org/cpython/file/'
    ...                           '{revision}/Lib/{package}/{path}#L{lineno}',
    ...                   revision='xxxx')
    'https://hg.python.org/cpython/file/xxxx/Lib/tty/tty.py#L18'
    """

    if revision is None:
        return
    if domain not in ("py", "pyx"):
        return
    if not info.get("module") or not info.get("fullname"):
        return

    class_name = info["fullname"].split(".")[0]
    module = __import__(info["module"], fromlist=[class_name])
    obj = attrgetter(info["fullname"])(module)

    # Unwrap the object to get the correct source
    # file in case that is wrapped by a decorator
    obj = inspect.unwrap(obj)

    try:
        fn = inspect.getsourcefile(obj)
    except Exception:
        fn = None
    if not fn:
        try:
            fn = inspect.getsourcefile(sys.modules[obj.__module__])
        except Exception:
            fn = None
    if not fn:
        return
    try:
        fn = os.path.relpath(fn, start=os.path.dirname(__import__(package).__file__))
    except ValueError:
        return None

    try:
        lineno = inspect.getsourcelines(obj)[1]
    except Exception:
        lineno = ""
    return url_fmt.format(revision=revision, package=package, path=fn, lineno=lineno)