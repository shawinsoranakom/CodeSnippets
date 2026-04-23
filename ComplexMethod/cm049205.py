def write(self, vals):
        fields_to_sync = [x for x in vals if x in self._get_microsoft_synced_fields()]
        if fields_to_sync and 'need_sync_m' not in vals and self.env.user._get_microsoft_sync_status() == "sync_active":
            vals['need_sync_m'] = True

        result = super().write(vals)

        if self.env.user._get_microsoft_sync_status() != "sync_paused":
            timeout = self._get_microsoft_graph_timeout()

            for record in self:
                if record.need_sync_m and record.microsoft_id:
                    if not vals.get('active', True):
                        # We need to delete the event. Cancel is not sufficient. Errors may occur.
                        record._microsoft_delete(record._get_organizer(), record.microsoft_id, timeout=timeout)
                    elif fields_to_sync:
                        values = record._microsoft_values(fields_to_sync)
                        if not values:
                            continue
                        record._microsoft_patch(record._get_organizer(), record.microsoft_id, values, timeout=timeout)

        return result