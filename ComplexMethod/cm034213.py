def get_man_text(doc, collection_name='', plugin_type=''):
        # Create a copy so we don't modify the original
        doc = dict(doc)

        DocCLI.IGNORE = DocCLI.IGNORE + (context.CLIARGS['type'],)
        opt_indent = "        "
        base_indent = "  "
        text = []
        pad = display.columns * 0.20
        limit = max(display.columns - int(pad), 70)

        text.append("> %s %s (%s)" % (plugin_type.upper(), _format(doc.pop('plugin_name'), 'bold'), doc.pop('filename') or 'Jinja2'))

        if isinstance(doc['description'], list):
            descs = doc.pop('description')
        else:
            descs = [doc.pop('description')]

        text.append('')
        for desc in descs:
            text.append(DocCLI.warp_fill(DocCLI.tty_ify(desc), limit, initial_indent=base_indent, subsequent_indent=base_indent))

        if display.verbosity > 0:
            doc['added_in'] = DocCLI._format_version_added(doc.pop('version_added', 'historical'), doc.pop('version_added_collection', 'ansible-core'))

        if doc.get('deprecated', False):
            text.append(_format("DEPRECATED: ", 'bold', 'DEP'))
            if isinstance(doc['deprecated'], dict):
                if 'removed_at_date' not in doc['deprecated'] and 'version' in doc['deprecated'] and 'removed_in' not in doc['deprecated']:
                    doc['deprecated']['removed_in'] = doc['deprecated']['version']
                try:
                    text.append('\t' + C.config.get_deprecated_msg_from_config(doc['deprecated'], True, collection_name=collection_name))
                except KeyError as e:
                    raise AnsibleError("Invalid deprecation documentation structure.") from e
            else:
                text.append("%s" % doc['deprecated'])
            del doc['deprecated']

        if doc.pop('has_action', False):
            text.append("")
            text.append(_format("  * note:", 'bold') + " This module has a corresponding action plugin.")

        if doc.get('options', False):
            text.append("")
            text.append(_format("OPTIONS", 'bold') + " (%s indicates it is required):" % ("=" if C.ANSIBLE_NOCOLOR else 'red'))
            DocCLI.add_fields(text, doc.pop('options'), limit, opt_indent, man=(display.verbosity == 0))

        if doc.get('attributes', False):
            text.append("")
            text.append(_format("ATTRIBUTES:", 'bold'))
            for k in doc['attributes'].keys():
                text.append('')
                text.append(DocCLI.warp_fill(DocCLI.tty_ify(_format('%s:' % k, 'UNDERLINE')), limit - 6, initial_indent=opt_indent,
                                             subsequent_indent=opt_indent))
                text.append(DocCLI._indent_lines(DocCLI._dump_yaml(doc['attributes'][k]), opt_indent))
            del doc['attributes']

        if doc.get('notes', False):
            text.append("")
            text.append(_format("NOTES:", 'bold'))
            for note in doc['notes']:
                text.append(DocCLI.warp_fill(DocCLI.tty_ify(note), limit - 6,
                                             initial_indent=opt_indent[:-2] + "* ", subsequent_indent=opt_indent))
            del doc['notes']

        if doc.get('seealso', False):
            text.append("")
            text.append(_format("SEE ALSO:", 'bold'))
            DocCLI._add_seealso(text, doc['seealso'], limit=limit, opt_indent=opt_indent)
            del doc['seealso']

        if doc.get('requirements', False):
            text.append('')
            req = ", ".join(doc.pop('requirements'))
            text.append(_format("REQUIREMENTS:", 'bold') + "%s\n" % DocCLI.warp_fill(DocCLI.tty_ify(req), limit - 16, initial_indent="  ",
                        subsequent_indent=opt_indent))

        # Generic handler
        for k in sorted(doc):
            if not doc[k] or k in DocCLI.IGNORE:
                continue
            text.append('')
            header = _format(k.upper(), 'bold')
            if isinstance(doc[k], str):
                text.append('%s: %s' % (header, DocCLI.warp_fill(DocCLI.tty_ify(doc[k]), limit - (len(k) + 2), subsequent_indent=opt_indent)))
            elif isinstance(doc[k], (list, tuple)):
                text.append('%s: %s' % (header, ', '.join(doc[k])))
            else:
                # use empty indent since this affects the start of the yaml doc, not it's keys
                text.append('%s: ' % header + DocCLI._indent_lines(DocCLI._dump_yaml(doc[k]), ' ' * (len(k) + 2)))
            del doc[k]

        if doc.get('plainexamples', False):
            text.append('')
            text.append(_format("EXAMPLES:", 'bold'))
            if isinstance(doc['plainexamples'], str):
                text.append(doc.pop('plainexamples').strip())
            else:
                try:
                    text.append(yaml_dump(doc.pop('plainexamples'), indent=2, default_flow_style=False))
                except Exception as ex:
                    raise AnsibleParserError("Unable to parse examples section.") from ex

        if doc.get('returndocs', False):
            text.append('')
            text.append(_format("RETURN VALUES:", 'bold'))
            DocCLI.add_fields(text, doc.pop('returndocs'), limit, opt_indent, return_values=True, man=(display.verbosity == 0))

        text.append('\n')
        return "\n".join(text)