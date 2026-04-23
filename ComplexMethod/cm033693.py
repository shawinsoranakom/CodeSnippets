def filter_targets(self, targets: list[IntegrationTarget], exclude: set[str]) -> None:
        """Filter the list of targets, adding any which this host profile cannot support to the provided exclude list."""
        if self.controller and self.args.host_settings.controller_fallback and targets:
            affected_targets = [target.name for target in targets]
            reason = self.args.host_settings.controller_fallback.reason

            if reason == FallbackReason.ENVIRONMENT:
                exclude.update(affected_targets)
                display.warning(f'Excluding {self.host_type} tests since a fallback controller is in use: {", ".join(affected_targets)}')
            elif reason == FallbackReason.PYTHON:
                display.warning(f'Some {self.host_type} tests may be redundant since a fallback python is in use: {", ".join(affected_targets)}')

        if not self.allow_destructive and not self.is_managed:
            override_destructive = set(target for target in self.include_targets if target.startswith('destructive/'))
            override = [target.name for target in targets if override_destructive & set(target.aliases)]

            self.skip('destructive', 'which require --allow-destructive or prefixing with "destructive/" to run on unmanaged hosts', targets, exclude, override)

        if not self.args.allow_disabled:
            override_disabled = set(target for target in self.args.include if target.startswith('disabled/'))
            override = [target.name for target in targets if override_disabled & set(target.aliases)]

            self.skip('disabled', 'which require --allow-disabled or prefixing with "disabled/"', targets, exclude, override)

        if not self.args.allow_unsupported:
            override_unsupported = set(target for target in self.args.include if target.startswith('unsupported/'))
            override = [target.name for target in targets if override_unsupported & set(target.aliases)]

            self.skip('unsupported', 'which require --allow-unsupported or prefixing with "unsupported/"', targets, exclude, override)

        if not self.args.allow_unstable:
            override_unstable = set(target for target in self.args.include if target.startswith('unstable/'))

            if self.args.allow_unstable_changed:
                override_unstable |= set(self.args.metadata.change_description.focused_targets or [])

            override = [target.name for target in targets if override_unstable & set(target.aliases)]

            self.skip('unstable', 'which require --allow-unstable or prefixing with "unstable/"', targets, exclude, override)