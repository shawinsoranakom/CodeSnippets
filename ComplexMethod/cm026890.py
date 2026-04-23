def latest_version(self) -> str | None:
        """Latest version available for install."""
        # If we already run a pre-release, we consider being on the beta channel.
        # Offer beta version upgrade, unless stable is newer
        if (
            (beta := self.releases_coordinator.data.beta) is not None
            and (current := self.coordinator.data.info.version) is not None
            and (current.alpha or current.beta or current.release_candidate)
            and (
                (stable := self.releases_coordinator.data.stable) is None
                or (stable is not None and stable < beta and current > stable)
            )
        ):
            return str(beta)

        if (stable := self.releases_coordinator.data.stable) is not None:
            return str(stable)

        return None