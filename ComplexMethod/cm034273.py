def subset(self, subset_pattern):
        """
        Limits inventory results to a subset of inventory that matches a given
        pattern, such as to select a given geographic of numeric slice amongst
        a previous 'hosts' selection that only select roles, or vice versa.
        Corresponds to --limit parameter to ansible-playbook
        """
        if subset_pattern is None:
            self._subset = None
        else:
            subset_patterns = split_host_pattern(subset_pattern)
            results = []
            # allow Unix style @filename data
            for x in subset_patterns:
                if not x:
                    continue

                if x[0] == "@":
                    b_limit_file = to_bytes(x[1:])
                    if not os.path.exists(b_limit_file):
                        raise AnsibleError(u'Unable to find limit file %s' % b_limit_file)
                    if not os.path.isfile(b_limit_file):
                        raise AnsibleError(u'Limit starting with "@" must be a file, not a directory: %s' % b_limit_file)
                    with open(b_limit_file) as fd:
                        results.extend([to_text(l.strip()) for l in fd.read().split("\n")])
                else:
                    results.append(to_text(x))
            self._subset = results