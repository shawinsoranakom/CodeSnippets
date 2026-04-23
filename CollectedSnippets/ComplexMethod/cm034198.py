def _do_yaml_snippet(doc):
    text = []

    mdesc = DocCLI.tty_ify(doc['short_description'])
    module = doc.get('module')

    if module:
        # this is actually a usable task!
        text.append("- name: %s" % (mdesc))
        text.append("  %s:" % (module))
    else:
        # just a comment, hopefully useful yaml file
        text.append("# %s:" % doc.get('plugin', doc.get('name')))

    pad = 29
    subdent = '# '.rjust(pad + 2)
    limit = display.columns - pad

    for o in sorted(doc['options'].keys()):
        opt = doc['options'][o]
        if isinstance(opt['description'], str):
            desc = DocCLI.tty_ify(opt['description'])
        else:
            desc = DocCLI.tty_ify(" ".join(opt['description']))

        required = opt.get('required', False)
        if not isinstance(required, bool):
            raise ValueError("Incorrect value for 'Required', a boolean is needed: %s" % required)

        o = '%s:' % o
        if module:
            if required:
                desc = "(required) %s" % desc
            text.append("      %-20s   # %s" % (o, DocCLI.warp_fill(desc, limit, subsequent_indent=subdent)))
        else:
            if required:
                default = '(required)'
            else:
                default = opt.get('default', 'None')

            text.append("%s %-9s # %s" % (o, default, DocCLI.warp_fill(desc, limit, subsequent_indent=subdent, max_lines=3)))

    return text