def _filter(self, facts_dict, filter_spec):
        # assume filter_spec='' or filter_spec=[] is equivalent to filter_spec='*'
        if not filter_spec or filter_spec == '*':
            return facts_dict

        if is_string(filter_spec):
            filter_spec = [filter_spec]

        found = []
        for f in filter_spec:
            for x, y in facts_dict.items():
                if not f or fnmatch.fnmatch(x, f):
                    found.append((x, y))
                elif not f.startswith(('ansible_', 'facter', 'ohai')):
                    # try to match with ansible_ prefix added when non empty
                    g = 'ansible_%s' % f
                    if fnmatch.fnmatch(x, g):
                        found.append((x, y))
        return found