def group_members(self) -> list[str]:
        """List of players which are grouped together."""
        multiroom = self._bridge.multiroom
        if multiroom is None:
            return []

        shared_data = self.hass.data[DOMAIN][SHARED_DATA]
        leader_id: str | None = None
        followers = []

        # find leader and followers
        for ent_id, uuid in shared_data.entity_to_bridge.items():
            if uuid == multiroom.leader.device.uuid:
                leader_id = ent_id
            elif uuid in {f.device.uuid for f in multiroom.followers}:
                followers.append(ent_id)

        if TYPE_CHECKING:
            assert leader_id is not None
        return [leader_id, *followers]