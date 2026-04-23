def get_hosts(self, pattern="all", ignore_limits=False, ignore_restrictions=False, order=None):
        """
        Takes a pattern or list of patterns and returns a list of matching
        inventory host names, taking into account any active restrictions
        or applied subsets
        """

        hosts = []

        # Check if pattern already computed
        if isinstance(pattern, list):
            pattern_list = pattern[:]
        else:
            pattern_list = [pattern]

        if pattern_list:
            if not ignore_limits and self._subset:
                pattern_list.extend(self._subset)

            if not ignore_restrictions and self._restriction:
                pattern_list.extend(self._restriction)

            # This is only used as a hash key in the self._hosts_patterns_cache dict
            # a tuple is faster than stringifying
            pattern_hash = tuple(pattern_list)

            if pattern_hash not in self._hosts_patterns_cache:

                patterns = split_host_pattern(pattern)
                hosts = self._evaluate_patterns(patterns)

                # mainly useful for hostvars[host] access
                if not ignore_limits and self._subset:
                    # exclude hosts not in a subset, if defined
                    subset_uuids = set(s._uuid for s in self._evaluate_patterns(self._subset))
                    hosts = [h for h in hosts if h._uuid in subset_uuids]

                if not ignore_restrictions and self._restriction:
                    # exclude hosts mentioned in any restriction (ex: failed hosts)
                    hosts = [h for h in hosts if h.name in self._restriction]

                self._hosts_patterns_cache[pattern_hash] = deduplicate_list(hosts)

            # sort hosts list if needed (should only happen when called from strategy)
            if order in ['sorted', 'reverse_sorted']:
                hosts = sorted(self._hosts_patterns_cache[pattern_hash][:], key=attrgetter('name'), reverse=(order == 'reverse_sorted'))
            elif order == 'reverse_inventory':
                hosts = self._hosts_patterns_cache[pattern_hash][::-1]
            else:
                hosts = self._hosts_patterns_cache[pattern_hash][:]
                if order == 'shuffle':
                    shuffle(hosts)
                elif order not in [None, 'inventory']:
                    raise AnsibleOptionsError("Invalid 'order' specified for inventory hosts: %s" % order)

        return hosts