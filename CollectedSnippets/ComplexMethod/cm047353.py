def _fields_sync(self, values):
        """ Sync commercial fields and address fields from company and to children.
        Also synchronize address to parent. This somehow mimics related fields
        to the parent, with more control. This method should be called after
        updating values in cache e.g. self should contain new values.

        :param dict values: updated values, triggering sync
        """
        # 1. From UPSTREAM: sync from parent
        if values.get('parent_id') or values.get('type') == 'contact':
            # 1a. Commercial fields: sync if parent changed
            if values.get('parent_id'):
                self.sudo()._commercial_sync_from_company()
            # 1b. Address fields: sync if parent or use_parent changed *and* both are now set
            if self.parent_id and self.type == 'contact':
                if address_values := self.parent_id._get_address_values():
                    self._update_address(address_values)

        # 2. To UPSTREAM: sync parent address, as well as editable synchronized commercial fields
        address_to_upstream = (
            # parent is set, potential address update as contact address = parent address
            bool(self.parent_id) and bool(self.type == 'contact') and
            # address updated, or parent updated
            (any(field in values for field in self._address_fields()) or 'parent_id' in values) and
            # something is actually updated
            any(self[fname] != self.parent_id[fname] for fname in self._address_fields())
        )
        if address_to_upstream:
            new_address = self._get_address_values()
            self.parent_id.write(new_address)  # is going to trigger _fields_sync again
        commercial_to_upstream = (
            # has a parent and is not a commercial entity itself
            bool(self.parent_id) and (self.commercial_partner_id != self) and
            # actually updated, or parent updated
            (any(field in values for field in self._synced_commercial_fields()) or 'parent_id' in values) and
            # something is actually updated
            any(self[fname] != self.parent_id[fname] for fname in self._synced_commercial_fields())
        )
        if commercial_to_upstream:
            new_synced_commercials = self._get_synced_commercial_values()
            self.parent_id.write(new_synced_commercials)

        # 3. To DOWNSTREAM: sync children
        self._children_sync(values)