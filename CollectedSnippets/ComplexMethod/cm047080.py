def has_wheel_for(self, version, python_version, platform):
        if version is None:
            return (False, False, False)
        py_version_info = python_version.split('.')
        if len(py_version_info) == 2:
            py_version_info = (py_version_info[0], py_version_info[1], 0)
        releases = self.releases
        has_wheel_for_version = False
        has_any_wheel = False
        has_wheel_in_another_version = False
        platforms = None
        if platform == 'darwin':
            platforms = list(mac_platforms((15, 0), 'x86_64'))
        elif platform == 'win32':
            platforms = ['win32', 'win-amd64']
        else:
            assert platform == 'linux'

        target_python = TargetPython(
            platforms=platforms,
            py_version_info=py_version_info,
            abis=None,
            implementation=None,
        )
        le = LinkEvaluator(
            project_name=self.name,
            canonical_name=canonicalize_name(self.name),
            formats={"binary", "source"},
            target_python=target_python,
            allow_yanked=True,
            ignore_requires_python=False,
        )
        for release in releases[version]:
            if release['filename'].endswith('.whl'):
                has_any_wheel = True
            is_candidate, _result = le.evaluate_link(Link(
                comes_from=None,
                url=release['url'],
                requires_python=release['requires_python'],
                yanked_reason=release['yanked_reason'],
            ))
            if is_candidate:
                if release['filename'].endswith('.whl'):
                    has_wheel_for_version = has_wheel_in_another_version = True
                break

        if not has_wheel_for_version and has_any_wheel:
            # TODO, we should prefer a version matching the one from a distro
            for rel_version, rel in releases.items():
                for release in rel:
                    if not release['filename'].endswith('.whl'):
                        continue
                    if any(not s.isdigit() for s in rel_version.split('.')) or parse_version(rel_version) <= parse_version(version):
                        continue
                    is_candidate, _result = le.evaluate_link(Link(
                        comes_from=None,
                        url=release['url'],
                        requires_python=release['requires_python'],
                        yanked_reason=release['yanked_reason'],
                    ))
                    if is_candidate:
                        has_wheel_in_another_version = True
                        stderr.write(f'WARNING: Wheel found for {self.name} ({python_version} {platform}) in {rel_version}\n')
                        return (has_wheel_for_version, has_any_wheel, has_wheel_in_another_version)

        return (has_wheel_for_version, has_any_wheel, has_wheel_in_another_version)