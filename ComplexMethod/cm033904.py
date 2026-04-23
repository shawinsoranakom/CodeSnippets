def comment(text, style='plain', **kw):
    # Predefined comment types
    comment_styles = {
        'plain': {
            'decoration': '# '
        },
        'erlang': {
            'decoration': '% '
        },
        'c': {
            'decoration': '// '
        },
        'cblock': {
            'beginning': '/*',
            'decoration': ' * ',
            'end': ' */'
        },
        'xml': {
            'beginning': '<!--',
            'decoration': ' - ',
            'end': '-->'
        }
    }

    if style not in comment_styles:
        raise AnsibleTemplatePluginError(
            message=f"Invalid style {style!r}.",
            help_text=f"Available styles: {', '.join(comment_styles)}",
            obj=style,
        )

    # Pointer to the right comment type
    style_params = comment_styles[style]

    if 'decoration' in kw:
        prepostfix = kw['decoration']
    else:
        prepostfix = style_params['decoration']

    # Default params
    p = {
        'newline': '\n',
        'beginning': '',
        'prefix': (prepostfix).rstrip(),
        'prefix_count': 1,
        'decoration': '',
        'postfix': (prepostfix).rstrip(),
        'postfix_count': 1,
        'end': ''
    }

    # Update default params
    p.update(style_params)
    p.update(kw)

    # Compose substrings for the final string
    str_beginning = ''
    if p['beginning']:
        str_beginning = "%s%s" % (p['beginning'], p['newline'])
    str_prefix = ''
    if p['prefix']:
        if p['prefix'] != p['newline']:
            str_prefix = str(
                "%s%s" % (p['prefix'], p['newline'])) * int(p['prefix_count'])
        else:
            str_prefix = str(
                "%s" % (p['newline'])) * int(p['prefix_count'])
    str_text = ("%s%s" % (
        p['decoration'],
        # Prepend each line of the text with the decorator
        text.replace(
            p['newline'], "%s%s" % (p['newline'], p['decoration'])))).replace(
                # Remove trailing spaces when only decorator is on the line
                "%s%s" % (p['decoration'], p['newline']),
                "%s%s" % (p['decoration'].rstrip(), p['newline']))
    str_postfix = p['newline'].join(
        [''] + [p['postfix'] for x in range(p['postfix_count'])])
    str_end = ''
    if p['end']:
        str_end = "%s%s" % (p['newline'], p['end'])

    # Return the final string
    return "%s%s%s%s%s" % (
        str_beginning,
        str_prefix,
        str_text,
        str_postfix,
        str_end)