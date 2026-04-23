def doc(thing, title='Python Library Documentation: %s', forceload=0,
        output=None, is_cli=False):
    """Display text documentation, given an object or a path to an object."""
    if output is None:
        try:
            if isinstance(thing, str):
                what = thing
            else:
                what = getattr(thing, '__qualname__', None)
                if not isinstance(what, str):
                    what = getattr(thing, '__name__', None)
                    if not isinstance(what, str):
                        what = type(thing).__name__ + ' object'
            pager(render_doc(thing, title, forceload), f'Help on {what!s}')
        except ImportError as exc:
            if is_cli:
                raise
            print(exc)
    else:
        try:
            s = render_doc(thing, title, forceload, plaintext)
        except ImportError as exc:
            s = str(exc)
        output.write(s)