def filter_profiles[THostProfile: HostProfile](self, profiles: list[THostProfile], target: IntegrationTarget) -> list[THostProfile]:
        """Filter the list of profiles, returning only those which are not skipped for the given target."""
        profiles = super().filter_profiles(profiles, target)

        skipped_profiles = [profile for profile in profiles if any(skip in target.skips for skip in get_remote_skip_aliases(profile.config))]

        if skipped_profiles:
            configs: list[TRemoteConfig] = [profile.config for profile in skipped_profiles]
            display.warning(f'Excluding skipped hosts from inventory: {", ".join(config.name for config in configs)}')

        profiles = [profile for profile in profiles if profile not in skipped_profiles]

        return profiles