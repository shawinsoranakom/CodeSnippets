def _browser_impersonate_target(self):
        available_targets = self._downloader._get_available_impersonate_targets()
        if not available_targets:
            # impersonate=True gives a generic warning when no impersonation targets are available
            return True

        # Any browser target older than chrome-116 is 403'd by Datadome
        MIN_SUPPORTED_TARGET = ImpersonateTarget('chrome', '116', 'windows', '10')
        version_as_float = lambda x: float(x.version) if x.version else 0

        # Always try to use the newest Chrome target available
        filtered = sorted([
            target[0] for target in available_targets
            if target[0].client == 'chrome' and target[0].os in ('windows', 'macos')
        ], key=version_as_float)

        if not filtered or version_as_float(filtered[-1]) < version_as_float(MIN_SUPPORTED_TARGET):
            # All available targets are inadequate or newest available Chrome target is too old, so
            # warn the user to upgrade their dependency to a version with the minimum supported target
            return MIN_SUPPORTED_TARGET

        return filtered[-1]