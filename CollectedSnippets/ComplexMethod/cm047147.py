def __init__(self, spec):
        """ Parse the spec to determine tags to include and exclude. """
        parts = re.split(r',(?![^\[]*\])', spec)  # split on all comma not inside [] (not followed by ])
        filter_specs = [t.strip() for t in parts if t.strip()]
        self.exclude = set()
        self.include = set()
        self.parameters = OrderedSet()

        for filter_spec in filter_specs:
            match = self.filter_spec_re.match(filter_spec)
            if not match:
                _logger.error('Invalid tag %s', filter_spec)
                continue

            sign, tag, file_path, module, klass, method, parameters = match.groups()
            is_include = sign != '-'
            is_exclude = not is_include

            if not tag and is_include:
                # including /module:class.method implicitly requires 'standard'
                tag = 'standard'
            elif not tag or tag == '*':
                # '*' indicates all tests (instead of 'standard' tests only)
                tag = None
            test_filter = (tag, module, klass, method, file_path)

            if parameters:
                # we could check here that test supports negated parameters
                self.parameters.add((test_filter, ('-' if is_exclude else '+', parameters)))
                is_exclude = False

            if is_include:
                self.include.add(test_filter)
            if is_exclude:
                self.exclude.add(test_filter)

        if (self.exclude or self.parameters) and not self.include:
            self.include.add(('standard', None, None, None, None))