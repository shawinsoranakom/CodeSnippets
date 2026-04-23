def check_ci_group(
        self,
        targets: tuple[CompletionTarget, ...],
        find: list[str],
        find_incidental: t.Optional[list[str]] = None,
    ) -> list[SanityMessage]:
        """Check the CI groups set in the provided targets and return a list of messages with any issues found."""
        all_paths = set(target.path for target in targets)
        supported_paths = set(target.path for target in filter_targets(targets, find, errors=False))
        unsupported_paths = set(target.path for target in filter_targets(targets, [self.UNSUPPORTED], errors=False))

        if find_incidental:
            incidental_paths = set(target.path for target in filter_targets(targets, find_incidental, errors=False))
        else:
            incidental_paths = set()

        unassigned_paths = all_paths - supported_paths - unsupported_paths - incidental_paths
        conflicting_paths = supported_paths & unsupported_paths

        valid_aliases = '`, `'.join([f.strip('/') for f in find])
        unassigned_message = 'missing alias `%s` or `%s`' % (valid_aliases, self.UNSUPPORTED.strip('/'))
        conflicting_message = 'conflicting alias `%s` and `%s`' % (valid_aliases, self.UNSUPPORTED.strip('/'))

        messages = []

        for path in unassigned_paths:
            if path == 'test/integration/targets/ansible-test-container':
                continue  # special test target which uses group 6 -- nothing else should be in that group

            if path in (
                'test/integration/targets/dnf-oldest',
                'test/integration/targets/dnf-latest',
            ):
                continue  # special test targets which use group 7 -- nothing else should be in that group

            messages.append(SanityMessage(unassigned_message, '%s/aliases' % path))

        for path in conflicting_paths:
            messages.append(SanityMessage(conflicting_message, '%s/aliases' % path))

        return messages