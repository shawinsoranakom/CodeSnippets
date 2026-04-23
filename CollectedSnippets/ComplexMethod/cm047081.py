def get_version(self, package):
        """ Try to find which version of ``package`` is in Debian release {release}
        """
        package = SPECIAL.get(package, package)
        # try the python prefix first: some packages have a native of foreign $X and
        # either the bindings or a python equivalent at python-X, or just a name
        # collision
        prefixes = ['python-', '']
        if package.startswith('python'):
            prefixes = ['']
        for prefix in prefixes:
            try:
                res = json.load(urlopen(f'https://sources.debian.org/api/src/{prefix}{package}/'))
            except HTTPError:
                return 'failed'
            if res.get('error') is None:
                break
        if res.get('error'):
            return

        try:
            return next(
                parse_version(cleanup_debian_version(distr['version']))
                for distr in res['versions']
                if distr['area'] == 'main'
                if self._release.lower() in distr['suites']
            )
        except StopIteration:
            return