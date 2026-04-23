def _evaluate_patterns(self, patterns):
        """
        Takes a list of patterns and returns a list of matching host names,
        taking into account any negative and intersection patterns.
        """

        patterns = order_patterns(patterns)
        hosts = []

        for p in patterns:
            # avoid resolving a pattern that is a plain host
            if p in self._inventory.hosts:
                hosts.append(self._inventory.get_host(p))
            else:
                that = self._match_one_pattern(p)
                if p[0] == "!":
                    that = set(that)
                    hosts = [h for h in hosts if h not in that]
                elif p[0] == "&":
                    that = set(that)
                    hosts = [h for h in hosts if h in that]
                else:
                    existing_hosts = set(y.name for y in hosts)
                    hosts.extend([h for h in that if h.name not in existing_hosts])
        return hosts