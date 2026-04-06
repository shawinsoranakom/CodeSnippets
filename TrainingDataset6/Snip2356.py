def format_raw_script(raw_script):
    """Creates single script from a list of script parts.

    :type raw_script: [basestring]
    :rtype: basestring

    """
    if six.PY2:
        script = ' '.join(arg.decode('utf-8') for arg in raw_script)
    else:
        script = ' '.join(raw_script)

    return script.lstrip()