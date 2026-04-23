def run(self, terms, variables=None, **kwargs):
        ret = []

        self.set_options(var_options=variables, direct=kwargs)

        # populate options
        paramvals = self.get_options()

        if not terms:
            raise AnsibleError('Search key is required but was not found')

        for term in terms:
            kv = parse_kv(term)

            if '_raw_params' not in kv:
                raise AnsibleError('Search key is required but was not found')

            key = kv['_raw_params']

            # parameters override per term using k/v
            reset_params = False
            for name, value in kv.items():
                if name == '_raw_params':
                    continue
                if name not in paramvals:
                    raise ValueError(f'{name!r} is not a valid option')

                self._deprecate_inline_kv()
                self.set_option(name, value)
                reset_params = True

            if reset_params:
                paramvals = self.get_options()

            # default is just placeholder for real tab
            if paramvals['delimiter'] == 'TAB':
                paramvals['delimiter'] = "\t"

            lookupfile = self.find_file_in_search_path(variables, 'files', paramvals['file'])
            var = self.read_csv(lookupfile, key, paramvals['delimiter'], paramvals['encoding'], paramvals['default'], paramvals['col'], paramvals['keycol'])
            if var is not None:
                if isinstance(var, MutableSequence):
                    ret.extend(var)
                else:
                    ret.append(var)

        return ret