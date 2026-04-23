def filter_targets(self, targets: list[IntegrationTarget], exclude: set[str]) -> None:
        """Filter the list of targets, adding any which this host profile cannot support to the provided exclude list."""
        super().filter_targets(targets, exclude)

        if len(self.configs) > 1:
            host_skips = {host.name: get_remote_skip_aliases(host) for host in self.configs}

            # Skip only targets which skip all hosts.
            # Targets that skip only some hosts will be handled during inventory generation.
            skipped = [target.name for target in targets if all(any(skip in target.skips for skip in skips) for skips in host_skips.values())]

            if skipped:
                exclude.update(skipped)
                display.warning(f'Excluding tests which do not support {", ".join(host_skips.keys())}: {", ".join(skipped)}')
        else:
            skips = get_remote_skip_aliases(self.config)

            for skip, reason in skips.items():
                self.skip(skip, reason, targets, exclude)