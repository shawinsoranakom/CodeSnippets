def rebuild_bluesound_group(self) -> list[str]:
        """Rebuild the list of entities in speaker group."""
        if self.sync_status.leader is None and self.sync_status.followers is None:
            return []

        config_entries: list[BluesoundConfigEntry] = (
            self.hass.config_entries.async_entries(DOMAIN)
        )
        sync_status_list = [
            x.runtime_data.coordinator.data.sync_status for x in config_entries
        ]

        leader_sync_status: SyncStatus | None = None
        if self.sync_status.leader is None:
            leader_sync_status = self.sync_status
        else:
            required_id = f"{self.sync_status.leader.ip}:{self.sync_status.leader.port}"
            for sync_status in sync_status_list:
                if sync_status.id == required_id:
                    leader_sync_status = sync_status
                    break

        if leader_sync_status is None or leader_sync_status.followers is None:
            return []

        follower_ids = [f"{x.ip}:{x.port}" for x in leader_sync_status.followers]
        follower_names = [
            sync_status.name
            for sync_status in sync_status_list
            if sync_status.id in follower_ids
        ]
        follower_names.insert(0, leader_sync_status.name)
        return follower_names