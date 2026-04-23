def __init__(self, exc_type, exc_value, exc_traceback, *, limit=None,
            lookup_lines=True, capture_locals=False, compact=False,
            max_group_width=15, max_group_depth=10, save_exc_type=True, _seen=None):
        # NB: we need to accept exc_traceback, exc_value, exc_traceback to
        # permit backwards compat with the existing API, otherwise we
        # need stub thunk objects just to glue it together.
        # Handle loops in __cause__ or __context__.
        is_recursive_call = _seen is not None
        if _seen is None:
            _seen = set()
        _seen.add(id(exc_value))

        self.max_group_width = max_group_width
        self.max_group_depth = max_group_depth

        self.stack = StackSummary._extract_from_extended_frame_gen(
            _walk_tb_with_full_positions(exc_traceback),
            limit=limit, lookup_lines=lookup_lines,
            capture_locals=capture_locals)

        self._exc_type = exc_type if save_exc_type else None

        # Capture now to permit freeing resources: only complication is in the
        # unofficial API _format_final_exc_line
        self._str = _safe_string(exc_value, 'exception')
        try:
            self.__notes__ = getattr(exc_value, '__notes__', None)
        except Exception as e:
            self.__notes__ = [
                f'Ignored error getting __notes__: {_safe_string(e, '__notes__', repr)}']

        self._is_syntax_error = False
        self._have_exc_type = exc_type is not None
        if exc_type is not None:
            self.exc_type_qualname = exc_type.__qualname__
            self.exc_type_module = exc_type.__module__
        else:
            self.exc_type_qualname = None
            self.exc_type_module = None

        if exc_type and issubclass(exc_type, SyntaxError):
            # Handle SyntaxError's specially
            self.filename = exc_value.filename
            lno = exc_value.lineno
            self.lineno = str(lno) if lno is not None else None
            end_lno = exc_value.end_lineno
            self.end_lineno = str(end_lno) if end_lno is not None else None
            self.text = exc_value.text
            self.offset = exc_value.offset
            self.end_offset = exc_value.end_offset
            self.msg = exc_value.msg
            self._is_syntax_error = True
            self._exc_metadata = getattr(exc_value, "_metadata", None)
        elif exc_type and issubclass(exc_type, ImportError) and \
                getattr(exc_value, "name_from", None) is not None:
            wrong_name = getattr(exc_value, "name_from", None)
            suggestion = _compute_suggestion_error(exc_value, exc_traceback, wrong_name)
            if suggestion:
                if suggestion.isascii():
                    self._str += f". Did you mean: '{suggestion}'?"
                else:
                    self._str += f". Did you mean: '{suggestion}' ({suggestion!a})?"
        elif exc_type and issubclass(exc_type, ModuleNotFoundError):
            module_name = getattr(exc_value, "name", None)
            if module_name in sys.stdlib_module_names:
                message = _MISSING_STDLIB_MODULE_MESSAGES.get(
                    module_name,
                    f"Standard library module {module_name!r} was not found"
                )
                self._str = message
            elif sys.flags.no_site:
                self._str += (". Site initialization is disabled, did you forget to "
                    + "add the site-packages directory to sys.path "
                    + "or to enable your virtual environment?")
            elif abi_tag := _find_incompatible_extension_module(module_name):
                self._str += (
                    ". Although a module with this name was found for a "
                    f"different Python version ({abi_tag})."
                )
            else:
                suggestion = _compute_suggestion_error(exc_value, exc_traceback, module_name)
                if suggestion:
                    self._str += f". Did you mean: '{suggestion}'?"
        elif exc_type and issubclass(exc_type, AttributeError) and \
                getattr(exc_value, "name", None) is not None:
            wrong_name = getattr(exc_value, "name", None)
            suggestion = _compute_suggestion_error(exc_value, exc_traceback, wrong_name)
            if suggestion:
                if suggestion.isascii():
                    self._str += f". Did you mean '.{suggestion}' instead of '.{wrong_name}'?"
                else:
                    self._str += f". Did you mean '.{suggestion}' ({suggestion!a}) instead of '.{wrong_name}' ({wrong_name!a})?"
        elif exc_type and issubclass(exc_type, NameError) and \
                getattr(exc_value, "name", None) is not None:
            wrong_name = getattr(exc_value, "name", None)
            suggestion = _compute_suggestion_error(exc_value, exc_traceback, wrong_name)
            if suggestion:
                if suggestion.isascii():
                    self._str += f". Did you mean: '{suggestion}'?"
                else:
                    self._str += f". Did you mean: '{suggestion}' ({suggestion!a})?"
            if wrong_name is not None and wrong_name in sys.stdlib_module_names:
                if suggestion:
                    self._str += f" Or did you forget to import '{wrong_name}'?"
                else:
                    self._str += f". Did you forget to import '{wrong_name}'?"
        if lookup_lines:
            self._load_lines()
        self.__suppress_context__ = \
            exc_value.__suppress_context__ if exc_value is not None else False

        # Convert __cause__ and __context__ to `TracebackExceptions`s, use a
        # queue to avoid recursion (only the top-level call gets _seen == None)
        if not is_recursive_call:
            queue = [(self, exc_value)]
            while queue:
                te, e = queue.pop()
                if (e is not None and e.__cause__ is not None
                    and id(e.__cause__) not in _seen):
                    cause = TracebackException(
                        type(e.__cause__),
                        e.__cause__,
                        e.__cause__.__traceback__,
                        limit=limit,
                        lookup_lines=lookup_lines,
                        capture_locals=capture_locals,
                        max_group_width=max_group_width,
                        max_group_depth=max_group_depth,
                        _seen=_seen)
                else:
                    cause = None

                if compact:
                    need_context = (cause is None and
                                    e is not None and
                                    not e.__suppress_context__)
                else:
                    need_context = True
                if (e is not None and e.__context__ is not None
                    and need_context and id(e.__context__) not in _seen):
                    context = TracebackException(
                        type(e.__context__),
                        e.__context__,
                        e.__context__.__traceback__,
                        limit=limit,
                        lookup_lines=lookup_lines,
                        capture_locals=capture_locals,
                        max_group_width=max_group_width,
                        max_group_depth=max_group_depth,
                        _seen=_seen)
                else:
                    context = None

                if e is not None and isinstance(e, BaseExceptionGroup):
                    exceptions = []
                    for exc in e.exceptions:
                        texc = TracebackException(
                            type(exc),
                            exc,
                            exc.__traceback__,
                            limit=limit,
                            lookup_lines=lookup_lines,
                            capture_locals=capture_locals,
                            max_group_width=max_group_width,
                            max_group_depth=max_group_depth,
                            _seen=_seen)
                        exceptions.append(texc)
                else:
                    exceptions = None

                te.__cause__ = cause
                te.__context__ = context
                te.exceptions = exceptions
                if cause:
                    queue.append((te.__cause__, e.__cause__))
                if context:
                    queue.append((te.__context__, e.__context__))
                if exceptions:
                    queue.extend(zip(te.exceptions, e.exceptions))