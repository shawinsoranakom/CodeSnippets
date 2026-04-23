def log_stats(self):
        if not stats_logger.isEnabledFor(logging.INFO):
            return

        details = stats_logger.isEnabledFor(logging.DEBUG)
        stats_tree = collections.defaultdict(Stat)
        counts = collections.Counter()
        for test, stat in self.stats.items():
            r = _TEST_ID.match(test)
            if not r: # upgrade has tests at weird paths, ignore them
                continue

            stats_tree[r['module']] += stat
            counts[r['module']] += 1
            if details:
                stats_tree['%(module)s.%(class)s' % r] += stat
                stats_tree['%(module)s.%(class)s.%(method)s' % r] += stat

        if details:
            stats_logger.debug('Detailed Tests Report:\n%s', ''.join(
                f'\t{test}: {stats.time:.2f}s {stats.queries} queries\n'
                for test, stats in sorted(stats_tree.items())
            ))
        else:
            for module, stat in sorted(stats_tree.items()):
                stats_logger.info(
                    "%s: %d tests %.2fs %d queries",
                    module, counts[module],
                    stat.time, stat.queries
                )