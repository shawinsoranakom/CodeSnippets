def run(self, terms, variables=None, **kwargs):

        self.set_options(var_options=variables, direct=kwargs)

        missing = self.get_option('on_missing')
        ptype = self.get_option('plugin_type')
        pname = self.get_option('plugin_name')
        show_origin = self.get_option('show_origin')

        if (ptype or pname) and not (ptype and pname):
            raise AnsibleError('Both plugin_type and plugin_name are required, cannot use one without the other.')

        ret = []

        # primarily use task vars, but fallback to existing constants when needed
        var_context = ChainMap(variables, vars(C))

        for term in terms:
            if not isinstance(term, str):
                raise AnsibleError(f'Invalid setting identifier, {term!r} is not a {str}, its a {type(term)}.')

            result = Sentinel
            origin = None

            # plugin creates settings on load, we ensure that happens here
            if pname:
                # this is cached so not too expensive
                loader = getattr(plugin_loader, f'{ptype}_loader')
                p = loader.get(pname, class_only=True)
                if p is None:
                    raise AnsibleError(f"Unable to load {ptype} plugin {pname!r}.")
            try:
                result, origin = C.config.get_config_value_and_origin(term, plugin_type=ptype, plugin_name=pname, variables=var_context)
            except AnsibleUndefinedConfigEntry as e:
                match missing:
                    case 'error':
                        raise
                    case 'skip':
                        pass
                    case 'warn':
                        self._display.error_as_warning(msg=f"Skipping {term}.", exception=e)

            if result is not Sentinel:
                if show_origin:
                    ret.append([result, origin])
                else:
                    ret.append(result)
        return ret