def add_fields(text, fields, limit, opt_indent, return_values=False, base_indent='', man=False):

        for o in sorted(fields):
            # Create a copy so we don't modify the original (in case YAML anchors have been used)
            opt = dict(fields[o])

            # required is used as indicator and removed
            required = opt.pop('required', False)
            if not isinstance(required, bool):
                raise AnsibleError("Incorrect value for 'Required', a boolean is needed.: %s" % required)

            opt_leadin = '  '
            key = ''
            if required:
                if C.ANSIBLE_NOCOLOR:
                    opt_leadin = "="
                key = "%s%s %s" % (base_indent, opt_leadin, _format(o, 'bold', 'red'))
            else:
                if C.ANSIBLE_NOCOLOR:
                    opt_leadin = "-"
                key = "%s%s %s" % (base_indent, opt_leadin, _format(o, 'yellow'))

            # description is specifically formatted and can either be string or list of strings
            if 'description' not in opt:
                raise AnsibleError("All (sub-)options and return values must have a 'description' field", obj=o)
            text.append('')

            # TODO: push this to top of for and sort by size, create indent on largest key?
            inline_indent = ' ' * max((len(opt_indent) - len(o)) - len(base_indent), 2)
            extra_indent = base_indent + ' ' * (len(o) + 3)
            sub_indent = inline_indent + extra_indent
            if is_sequence(opt['description']):
                for entry_idx, entry in enumerate(opt['description'], 1):
                    if not isinstance(entry, str):
                        raise AnsibleError("Expected string in description of %s at index %s, got %s" % (o, entry_idx, type(entry)))
                    if entry_idx == 1:
                        text.append(key + DocCLI.warp_fill(DocCLI.tty_ify(entry), limit,
                                    initial_indent=inline_indent, subsequent_indent=sub_indent, initial_extra=len(extra_indent)))
                    else:
                        text.append(DocCLI.warp_fill(DocCLI.tty_ify(entry), limit, initial_indent=sub_indent, subsequent_indent=sub_indent))
            else:
                if not isinstance(opt['description'], str):
                    raise AnsibleError("Expected string in description of %s, got %s" % (o, type(opt['description'])))
                text.append(key + DocCLI.warp_fill(DocCLI.tty_ify(opt['description']), limit,
                            initial_indent=inline_indent, subsequent_indent=sub_indent, initial_extra=len(extra_indent)))
            del opt['description']

            suboptions = []
            for subkey in ('options', 'suboptions', 'contains', 'spec'):
                if subkey in opt:
                    suboptions.append((subkey, opt.pop(subkey)))

            if not required and not return_values and 'default' not in opt:
                opt['default'] = None

            # sanitize config items
            conf = {}
            for config in ('env', 'ini', 'yaml', 'vars', 'keyword'):
                if config in opt and opt[config]:
                    # Create a copy so we don't modify the original (in case YAML anchors have been used)
                    conf[config] = [dict(item) for item in opt.pop(config)]
                    for ignore in DocCLI.IGNORE:
                        for item in conf[config]:
                            if display.verbosity > 0 and 'version_added' in item:
                                item['added_in'] = DocCLI._format_version_added(item['version_added'], item.get('version_added_colleciton', 'ansible-core'))
                            if ignore in item:
                                del item[ignore]

            # reformat cli options
            if 'cli' in opt and opt['cli']:
                conf['cli'] = []
                for cli in opt['cli']:
                    if 'option' not in cli:
                        conf['cli'].append({'name': cli['name'], 'option': '--%s' % cli['name'].replace('_', '-')})
                    else:
                        conf['cli'].append(cli)
                del opt['cli']

            # add custom header for conf
            if conf:
                text.append(DocCLI._indent_lines(DocCLI._dump_yaml({'set_via': conf}), opt_indent))

            # these we handle at the end of generic option processing
            version_added = opt.pop('version_added', None)
            version_added_collection = opt.pop('version_added_collection', None)

            # general processing for options
            for k in sorted(opt):
                if k.startswith('_'):
                    continue

                if is_sequence(opt[k]):
                    text.append(DocCLI._indent_lines('%s: %s' % (k, DocCLI._dump_yaml(opt[k], flow_style=True)), opt_indent))
                else:
                    text.append(DocCLI._indent_lines(DocCLI._dump_yaml({k: opt[k]}), opt_indent))

            if version_added and not man:
                text.append("%sadded in: %s" % (opt_indent, DocCLI._format_version_added(version_added, version_added_collection)))

            for subkey, subdata in suboptions:
                text.append("%s%s:" % (opt_indent, subkey))
                DocCLI.add_fields(text, subdata, limit, opt_indent + '  ', return_values, opt_indent)