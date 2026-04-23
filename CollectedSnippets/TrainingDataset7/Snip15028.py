def check_python_domain_in_roles(file, lines, options=None):
    """
    :py: indicates the Python language domain. This means code writen in
    Python, not Python built-ins in particular.

    Bad:    :py:class:`email.message.EmailMessage`
    Good:   :class:`email.message.EmailMessage`
    """
    for lno, line in enumerate(lines, start=1):
        role = _PYTHON_DOMAIN.search(line)
        if role:
            yield lno, f":py domain is the default and can be omitted {role.group(0)!r}"