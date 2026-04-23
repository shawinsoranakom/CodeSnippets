def int_list_validator(sep=",", message=None, code="invalid", allow_negative=False):
    regexp = _lazy_re_compile(
        r"^%(neg)s\d+(?:%(sep)s%(neg)s\d+)*\Z"
        % {
            "neg": "(-)?" if allow_negative else "",
            "sep": re.escape(sep),
        }
    )
    return RegexValidator(regexp, message=message, code=code)