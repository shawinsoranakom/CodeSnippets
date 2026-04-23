def get_or_allocate_iid(
        self,
        aid: int,
        service_uuid: UUID,
        service_unique_id: str | None,
        char_uuid: UUID | None,
        char_unique_id: str | None,
    ) -> int:
        """Generate a stable iid."""
        service_hap_type: str = uuid_to_hap_type(service_uuid)
        char_hap_type: str | None = uuid_to_hap_type(char_uuid) if char_uuid else None
        # Allocation key must be a string since we are saving it to JSON
        allocation_key = (
            f"{service_hap_type}_{service_unique_id or ''}_"
            f"{char_hap_type or ''}_{char_unique_id or ''}"
        )
        # AID must be a string since JSON keys cannot be int
        aid_str = str(aid)
        accessory_allocation = self.allocations.setdefault(aid_str, {})
        accessory_allocated_iids = self.allocated_iids.setdefault(aid_str, [1])
        if service_hap_type == ACCESSORY_INFORMATION_SERVICE and char_uuid is None:
            return 1
        if allocation_key in accessory_allocation:
            return accessory_allocation[allocation_key]
        if accessory_allocated_iids:
            allocated_iid = accessory_allocated_iids[-1] + 1
        else:
            allocated_iid = 2
        accessory_allocation[allocation_key] = allocated_iid
        accessory_allocated_iids.append(allocated_iid)
        self._async_schedule_save()
        return allocated_iid