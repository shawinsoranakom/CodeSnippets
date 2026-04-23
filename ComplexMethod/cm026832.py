def get_or_allocate_aid(self, unique_id: str | None, entity_id: str) -> int:
        """Allocate (and return) a new aid for an accessory."""
        if unique_id and unique_id in self.allocations:
            return self.allocations[unique_id]
        if entity_id in self.allocations:
            return self.allocations[entity_id]

        for aid in _generate_aids(unique_id, entity_id):
            if aid in INVALID_AIDS:
                continue
            if aid not in self.allocated_aids:
                # Prefer the unique_id over the entitiy_id
                storage_key = unique_id or entity_id
                self.allocations[storage_key] = aid
                self.allocated_aids.add(aid)
                self.async_schedule_save()
                return aid

        raise ValueError(
            f"Unable to generate unique aid allocation for {entity_id} [{unique_id}]"
        )