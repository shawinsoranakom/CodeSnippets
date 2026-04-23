def ci_test_groups(self) -> dict[str, list[int]]:
        """Return a dictionary of CI test names and their group(s)."""
        if not self._ci_test_groups:
            test_groups: dict[str, set[int]] = {}

            for stage in self._ci_config['stages']:
                for job in stage['jobs']:
                    if job.get('template') != 'templates/matrix.yml':
                        continue

                    parameters = job['parameters']

                    groups = parameters.get('groups', [])
                    test_format = parameters.get('testFormat', '{0}')
                    test_group_format = parameters.get('groupFormat', '{0}/{{1}}')

                    for target in parameters['targets']:
                        test = target.get('test') or target.get('name')

                        if groups:
                            tests_formatted = [test_group_format.format(test_format).format(test, group) for group in groups]
                        else:
                            tests_formatted = [test_format.format(test)]

                        for test_formatted in tests_formatted:
                            parts = test_formatted.split('/')
                            key = parts[0]

                            if key in ('sanity', 'units'):
                                continue

                            try:
                                group = int(parts[-1])
                            except ValueError:
                                continue

                            if group < 1 or group > 99:
                                continue

                            group_set = test_groups.setdefault(key, set())
                            group_set.add(group)

            self._ci_test_groups = dict((key, sorted(value)) for key, value in test_groups.items())

        return self._ci_test_groups