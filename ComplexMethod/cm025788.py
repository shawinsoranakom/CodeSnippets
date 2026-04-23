def rebuild_group_members(self) -> list[str] | None:
        """Get list of group members. Leader is always first."""
        if self.sync_status.leader is None and self.sync_status.followers is None:
            return None

        entity_ids_with_sync_status = self._entity_ids_with_sync_status()

        leader_entity_id = None
        followers = None
        if self.sync_status.followers is not None:
            leader_entity_id = self.entity_id
            followers = self.sync_status.followers
        elif self.sync_status.leader is not None:
            leader_id = f"{self.sync_status.leader.ip}:{self.sync_status.leader.port}"
            for entity_id, sync_status in entity_ids_with_sync_status.items():
                if sync_status.id == leader_id:
                    leader_entity_id = entity_id
                    followers = sync_status.followers
                    break

        if leader_entity_id is None or followers is None:
            return None

        grouped_entity_ids = [leader_entity_id]
        for follower in followers:
            follower_id = f"{follower.ip}:{follower.port}"
            entity_ids = [
                entity_id
                for entity_id, sync_status in entity_ids_with_sync_status.items()
                if sync_status.id == follower_id
            ]
            match entity_ids:
                case [entity_id]:
                    grouped_entity_ids.append(entity_id)

        return grouped_entity_ids