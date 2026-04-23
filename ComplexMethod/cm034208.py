def run(self):

        super(DocCLI, self).run()

        basedir = context.CLIARGS['basedir']
        plugin_type = context.CLIARGS['type'].lower()
        do_json = context.CLIARGS['json_format'] or context.CLIARGS['dump']
        listing = context.CLIARGS['list_files'] or context.CLIARGS['list_dir']
        no_fail = bool(not context.CLIARGS['no_fail_on_errors'])

        if context.CLIARGS['list_files']:
            content = 'files'
        elif context.CLIARGS['list_dir']:
            content = 'dir'
        else:
            content = None

        docs = {}

        if basedir:
            AnsibleCollectionConfig.playbook_paths = basedir

        if plugin_type not in TARGET_OPTIONS:
            raise AnsibleOptionsError("Unknown or undocumentable plugin type: %s" % plugin_type)

        if context.CLIARGS['dump']:
            # we always dump all types, ignore restrictions
            ptypes = TARGET_OPTIONS
            docs['all'] = {}
            for ptype in ptypes:

                if ptype == 'role':
                    roles = self._create_role_list(fail_on_errors=no_fail)
                    docs['all'][ptype] = self._create_role_doc(roles.keys(), context.CLIARGS['entry_point'], fail_on_errors=no_fail)
                elif ptype == 'keyword':
                    names = DocCLI._list_keywords()
                    docs['all'][ptype] = DocCLI._get_keywords_docs(names.keys())
                else:
                    plugin_names = self._list_plugins(ptype, None)
                    docs['all'][ptype] = self._get_plugins_docs(ptype, plugin_names, fail_ok=(ptype in ('test', 'filter')), fail_on_errors=no_fail)
                    # reset list after each type to avoid pollution
        elif listing:
            if plugin_type == 'keyword':
                docs = DocCLI._list_keywords()
            elif plugin_type == 'role':
                docs = self._create_role_list(fail_on_errors=False)
            else:
                docs = self._list_plugins(plugin_type, content)
        else:
            # here we require a name
            if len(context.CLIARGS['args']) == 0:
                raise AnsibleOptionsError("Missing name(s), incorrect options passed for detailed documentation.")

            if plugin_type == 'keyword':
                docs = DocCLI._get_keywords_docs(context.CLIARGS['args'])
            elif plugin_type == 'role':
                docs = self._create_role_doc(context.CLIARGS['args'], context.CLIARGS['entry_point'], fail_on_errors=no_fail)
            else:
                # display specific plugin docs
                docs = self._get_plugins_docs(plugin_type, context.CLIARGS['args'])

        # Display the docs
        if do_json:
            jdump(docs)
        else:
            text = []
            if plugin_type in C.DOCUMENTABLE_PLUGINS:
                if listing and docs:
                    self.display_plugin_list(docs)
                elif context.CLIARGS['show_snippet']:
                    if plugin_type not in SNIPPETS:
                        raise AnsibleError('Snippets are only available for the following plugin'
                                           ' types: %s' % ', '.join(SNIPPETS))

                    for plugin, doc_data in docs.items():
                        try:
                            textret = DocCLI.format_snippet(plugin, plugin_type, doc_data['doc'])
                        except ValueError as e:
                            display.warning("Unable to construct a snippet for"
                                            " '{0}': {1}".format(plugin, to_text(e)))
                        else:
                            text.append(textret)
                else:
                    # Some changes to how plain text docs are formatted
                    for plugin, doc_data in docs.items():

                        textret = DocCLI.format_plugin_doc(plugin, plugin_type,
                                                           doc_data['doc'], doc_data['examples'],
                                                           doc_data['return'], doc_data['metadata'])
                        if textret:
                            text.append(textret)
                        else:
                            display.warning("No valid documentation was retrieved from '%s'" % plugin)

            elif plugin_type == 'role':
                if context.CLIARGS['list_dir'] and docs:
                    self._display_available_roles(docs)
                elif docs:
                    self._display_role_doc(docs)

            elif docs:
                text = DocCLI.tty_ify(DocCLI._dump_yaml(docs))

            if text:
                DocCLI.pager(''.join(text))

        return 0