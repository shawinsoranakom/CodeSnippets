def state_attributes(self) -> dict[str, Any] | None:
        """Return state attributes."""
        if (release_summary := self.release_summary) is not None:
            release_summary = release_summary[:255]

        # If entity supports progress, return the in_progress value.
        # Otherwise, we use the internal progress value.
        if UpdateEntityFeature.PROGRESS in self.supported_features:
            in_progress = self.in_progress
            update_percentage = self.update_percentage if in_progress else None
            if type(in_progress) is not bool and isinstance(in_progress, int):
                update_percentage = in_progress  # type: ignore[unreachable]
                in_progress = True
        else:
            in_progress = self.__in_progress
            update_percentage = None

        installed_version = self.installed_version
        latest_version = self.latest_version
        skipped_version = self.__skipped_version
        # Clear skipped version in case it matches the current installed
        # version or the latest version diverged.
        if (installed_version is not None and skipped_version == installed_version) or (
            latest_version is not None and skipped_version != latest_version
        ):
            skipped_version = None
            self.__skipped_version = None

        return {
            ATTR_AUTO_UPDATE: self.auto_update,
            ATTR_DISPLAY_PRECISION: self.display_precision,
            ATTR_INSTALLED_VERSION: installed_version,
            ATTR_IN_PROGRESS: in_progress,
            ATTR_LATEST_VERSION: latest_version,
            ATTR_RELEASE_SUMMARY: release_summary,
            ATTR_RELEASE_URL: self.release_url,
            ATTR_SKIPPED_VERSION: skipped_version,
            ATTR_TITLE: self.title,
            ATTR_UPDATE_PERCENTAGE: update_percentage,
        }