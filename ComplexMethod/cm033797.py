def _validate_option_docs(self, options, context=None):
        if not isinstance(options, dict):
            return
        if context is None:
            context = []

        normalized_option_alias_names = dict()

        def add_option_alias_name(name, option_name):
            normalized_name = str(name).lower()
            normalized_option_alias_names.setdefault(normalized_name, {}).setdefault(option_name, set()).add(name)

        for option, data in options.items():
            if 'suboptions' in data:
                self._validate_option_docs(data.get('suboptions'), context + [option])
            add_option_alias_name(option, option)
            if 'aliases' in data and isinstance(data['aliases'], list):
                for alias in data['aliases']:
                    add_option_alias_name(alias, option)

        for normalized_name, options in normalized_option_alias_names.items():
            if len(options) < 2:
                continue

            what = []
            for option_name, names in sorted(options.items()):
                if option_name in names:
                    what.append("option '%s'" % option_name)
                else:
                    what.append("alias '%s' of option '%s'" % (sorted(names)[0], option_name))
            msg = "Multiple options/aliases"
            if context:
                msg += " found in %s" % " -> ".join(context)
            msg += " are equal up to casing: %s" % ", ".join(what)
            self.reporter.error(
                path=self.object_path,
                code='option-equal-up-to-casing',
                msg=msg,
            )