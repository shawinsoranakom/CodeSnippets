def regex_search(value, regex, *args, **kwargs):
    """ Perform re.search and return the list of matches or a backref """

    value = to_text(value, errors='surrogate_or_strict', nonstring='simplerepr')

    groups = list()
    for arg in args:
        if arg.startswith('\\g'):
            match = re.match(r'\\g<(\S+)>', arg).group(1)
            groups.append(match)
        elif arg.startswith('\\'):
            match = int(re.match(r'\\(\d+)', arg).group(1))
            groups.append(match)
        else:
            raise AnsibleFilterError('Unknown argument')

    flags = 0
    if kwargs.get('ignorecase'):
        flags |= re.I
    if kwargs.get('multiline'):
        flags |= re.M

    match = re.search(regex, value, flags)
    if match:
        if not groups:
            return match.group()
        else:
            items = list()
            for item in groups:
                items.append(match.group(item))
            return items