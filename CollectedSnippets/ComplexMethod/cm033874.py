def _load_config_defs(self, name, module, path):
        """ Reads plugin docs to find configuration setting definitions, to push to config manager for later use """

        # plugins w/o class name don't support config
        if self.class_name:
            type_name = get_plugin_class(self.class_name)

            # if type name != 'module_doc_fragment':
            if type_name in C.CONFIGURABLE_PLUGINS and not C.config.has_configuration_definition(type_name, name):
                # trust-tagged source propagates to loaded values; expressions and templates in config require trust
                documentation_source = _tags.TrustedAsTemplate().tag(getattr(module, 'DOCUMENTATION', ''))
                try:
                    dstring = yaml.load(_tags.Origin(path=path).tag(documentation_source), Loader=AnsibleLoader)
                except ParserError as e:
                    raise AnsibleError(f"plugin {name} has malformed documentation!") from e

                # TODO: allow configurable plugins to use sidecar
                # if not dstring:
                #     filename, cn = find_plugin_docfile( name, type_name, self, [os.path.dirname(path)], C.YAML_DOC_EXTENSIONS)

                if dstring:
                    add_fragments(dstring, path, fragment_loader=fragment_loader, is_module=(type_name == 'module'), section='DOCUMENTATION')

                    if 'options' in dstring and isinstance(dstring['options'], dict):
                        C.config.initialize_plugin_configuration_definitions(type_name, name, dstring['options'])
                        display.debug('Loaded config def from plugin (%s/%s)' % (type_name, name))