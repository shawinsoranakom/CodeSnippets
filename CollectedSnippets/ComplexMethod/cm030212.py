def _compute_suggestion_error(exc_value, tb, wrong_name):
    if wrong_name is None or not isinstance(wrong_name, str):
        return None
    not_normalized = False
    if not wrong_name.isascii():
        from unicodedata import normalize
        normalized_name = normalize('NFKC', wrong_name)
        if normalized_name != wrong_name:
            not_normalized = True
            wrong_name = normalized_name
    if isinstance(exc_value, AttributeError):
        obj = exc_value.obj
        try:
            d = _get_safe___dir__(obj)
            hide_underscored = (wrong_name[:1] != '_')
            if hide_underscored and tb is not None:
                while tb.tb_next is not None:
                    tb = tb.tb_next
                frame = tb.tb_frame
                if 'self' in frame.f_locals and frame.f_locals['self'] is obj:
                    hide_underscored = False
            if hide_underscored:
                d = [x for x in d if x[:1] != '_']
        except Exception:
            return None
    elif isinstance(exc_value, ModuleNotFoundError):
        try:
            if parent_name := wrong_name.rpartition('.')[0]:
                parent = importlib.util.find_spec(parent_name)
            else:
                parent = None
            d = []
            for finder in sys.meta_path:
                if discover := getattr(finder, 'discover', None):
                    d += [spec.name for spec in discover(parent)]
        except Exception:
            return None
    elif isinstance(exc_value, ImportError):
        try:
            mod = __import__(exc_value.name)
            d = _get_safe___dir__(mod)
            if wrong_name[:1] != '_':
                d = [x for x in d if x[:1] != '_']
        except Exception:
            return None
    else:
        assert isinstance(exc_value, NameError)
        # find most recent frame
        if tb is None:
            return None
        while tb.tb_next is not None:
            tb = tb.tb_next
        frame = tb.tb_frame
        d = (
            list(frame.f_locals)
            + list(frame.f_globals)
            + list(frame.f_builtins)
        )
        d = [x for x in d if isinstance(x, str)]
        if not_normalized and wrong_name in d:
            return wrong_name

        # Check first if we are in a method and the instance
        # has the wrong name as attribute
        if 'self' in frame.f_locals:
            self = frame.f_locals['self']
            try:
                has_wrong_name = hasattr(self, wrong_name)
            except Exception:
                has_wrong_name = False
            if has_wrong_name:
                return f"self.{wrong_name}"

    if not_normalized and wrong_name in d:
        return wrong_name
    try:
        import _suggestions
    except ImportError:
        pass
    else:
        suggestion = _suggestions._generate_suggestions(d, wrong_name)
        if suggestion:
            return suggestion

    # Compute closest match

    if len(d) > _MAX_CANDIDATE_ITEMS:
        return None
    wrong_name_len = len(wrong_name)
    if wrong_name_len > _MAX_STRING_SIZE:
        return None
    best_distance = wrong_name_len
    suggestion = None
    for possible_name in d:
        if possible_name == wrong_name:
            # A missing attribute is "found". Don't suggest it (see GH-88821).
            continue
        # No more than 1/3 of the involved characters should need changed.
        max_distance = (len(possible_name) + wrong_name_len + 3) * _MOVE_COST // 6
        # Don't take matches we've already beaten.
        max_distance = min(max_distance, best_distance - 1)
        current_distance = _levenshtein_distance(wrong_name, possible_name, max_distance)
        if current_distance > max_distance:
            continue
        if not suggestion or current_distance < best_distance:
            suggestion = possible_name
            best_distance = current_distance

    # If no direct attribute match found, check for nested attributes
    if not suggestion and isinstance(exc_value, AttributeError):
        with suppress(Exception):
            nested_suggestion = _check_for_nested_attribute(exc_value.obj, wrong_name, d)
            if nested_suggestion:
                return nested_suggestion

    return suggestion