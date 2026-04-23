def run(self, terms, variables=None, **kwargs):

        self.set_options(var_options=variables, direct=kwargs)
        paramvals = self.get_options()

        self.cp = configparser.ConfigParser(
            allow_no_value=paramvals.get('allow_no_value', paramvals.get('allow_none')),
            interpolation=configparser.BasicInterpolation() if paramvals.get('interpolation') else None,
        )
        if paramvals['case_sensitive']:
            self.cp.optionxform = to_native

        ret = []
        for term in terms:

            key = term
            # parameters specified?
            if '=' in term or ' ' in term.strip():
                self._deprecate_inline_kv()
                params = _parse_params(term, paramvals)
                param = None
                try:
                    updated_key = False
                    updated_options = False
                    for param in params:
                        if '=' in param:
                            name, value = param.split('=')
                            if name not in paramvals:
                                raise AnsibleError(f"{name!r} is not a valid option.")
                            self.set_option(name, value)
                            updated_options = True
                        elif key == term:
                            # only take first, this format never supported multiple keys inline
                            key = param
                            updated_key = True
                    if updated_options:
                        paramvals = self.get_options()
                except ValueError as ex:
                    # bad params passed
                    raise ValueError(f"Could not use {param!r} from {params!r}.") from ex
                if not updated_key:
                    raise ValueError(f"No key to look up was provided as first term within string inline options: {term}")
                    # only passed options in inline string

            # TODO: look to use cache to avoid redoing this for every term if they use same file
            # Retrieve file path
            path = self.find_file_in_search_path(variables, 'files', paramvals['file'])

            # Create StringIO later used to parse ini
            config = StringIO()
            # Special case for java properties
            if paramvals['type'] == "properties":
                config.write(u'[java_properties]\n')
                paramvals['section'] = 'java_properties'

            contents = self._loader.get_text_file_contents(path, encoding=paramvals['encoding'])
            config.write(contents)
            config.seek(0, os.SEEK_SET)

            try:
                self.cp.read_file(config)
            except configparser.DuplicateOptionError as ex:
                raise ValueError(f"Duplicate option in {paramvals['file']!r}.") from ex

            try:
                var = self.get_value(key, paramvals['section'], paramvals['default'], paramvals['re'])
            except configparser.NoSectionError:
                raise ValueError(f"No section {paramvals['section']!r} in {paramvals['file']!r}.") from None

            if var is not None:
                if isinstance(var, MutableSequence):
                    for v in var:
                        ret.append(v)
                else:
                    ret.append(var)

        return ret