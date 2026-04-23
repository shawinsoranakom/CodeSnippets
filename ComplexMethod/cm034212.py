def get_role_man_text(self, role, role_json):
        """Generate text for the supplied role suitable for display.

        This is similar to get_man_text(), but roles are different enough that we have
        a separate method for formatting their display.

        :param role: The role name.
        :param role_json: The JSON for the given role as returned from _create_role_doc().

        :returns: A array of text suitable for displaying to screen.
        """
        text = []
        opt_indent = "          "
        pad = display.columns * 0.20
        limit = max(display.columns - int(pad), 70)

        text.append("> ROLE: %s (%s)" % (_format(role, 'BOLD'), role_json.get('path')))

        for entry_point in role_json['entry_points']:
            doc = role_json['entry_points'][entry_point]
            desc = ''
            if doc.get('short_description'):
                desc = "- %s" % (doc.get('short_description'))
            text.append('')
            text.append("ENTRY POINT: %s %s" % (_format(entry_point, "BOLD"), desc))
            text.append('')

            if version_added := doc.pop('version_added', None):
                text.append(_format("ADDED IN:", 'bold') + " %s\n" % DocCLI._format_version_added(version_added))

            if doc.get('description'):
                if isinstance(doc['description'], list):
                    descs = doc['description']
                else:
                    descs = [doc['description']]
                for desc in descs:
                    text.append("%s" % DocCLI.warp_fill(DocCLI.tty_ify(desc), limit, initial_indent=opt_indent, subsequent_indent=opt_indent))
                text.append('')

            if doc.get('options'):
                text.append(_format("Options", 'bold') + " (%s indicates it is required):" % ("=" if C.ANSIBLE_NOCOLOR else 'red'))
                DocCLI.add_fields(text, doc.pop('options'), limit, opt_indent)

            if notes := doc.pop('notes', False):
                text.append("")
                text.append(_format("NOTES:", 'bold'))
                for note in notes:
                    text.append(DocCLI.warp_fill(DocCLI.tty_ify(note), limit - 6,
                                                 initial_indent=opt_indent[:-2] + "* ", subsequent_indent=opt_indent))

            if seealso := doc.pop('seealso', False):
                text.append("")
                text.append(_format("SEE ALSO:", 'bold'))
                DocCLI._add_seealso(text, seealso, limit=limit, opt_indent=opt_indent)

            # generic elements we will handle identically
            for k in ('author',):
                if k not in doc:
                    continue
                text.append('')
                if isinstance(doc[k], str):
                    text.append('%s: %s' % (k.upper(), DocCLI.warp_fill(DocCLI.tty_ify(doc[k]),
                                            limit - (len(k) + 2), subsequent_indent=opt_indent)))
                elif isinstance(doc[k], (list, tuple)):
                    text.append('%s: %s' % (k.upper(), ', '.join(doc[k])))
                else:
                    # use empty indent since this affects the start of the yaml doc, not it's keys
                    text.append(DocCLI._indent_lines(DocCLI._dump_yaml({k.upper(): doc[k]}), ''))

            if doc.get('examples', False):
                text.append('')
                text.append(_format("EXAMPLES:", 'bold'))
                if isinstance(doc['examples'], str):
                    text.append(doc.pop('examples').strip())
                else:
                    try:
                        text.append(yaml_dump(doc.pop('examples'), indent=2, default_flow_style=False))
                    except Exception as e:
                        raise AnsibleParserError("Unable to parse examples section.") from e

        return text