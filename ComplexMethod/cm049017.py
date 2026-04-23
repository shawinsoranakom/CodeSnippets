def search_or_create(self, vals_list):
        """Get existing or newly created records matching vals_list items in preserved order supporting duplicates."""
        if not isinstance(vals_list, list):
            _logger.warning("Deprecated usage of LinkTracker.search_or_create which now expects a list of dictionaries as input.")
            vals_list = [vals_list]

        def _format_key(obj):
            """Generate unique 'key' of trackers, allowing to find duplicates."""
            return tuple(
                (field_name, obj[field_name].id if isinstance(obj[field_name], models.BaseModel) else obj[field_name])
                for field_name in LINK_TRACKER_UNIQUE_FIELDS
            )

        def _format_key_domain(field_values):
            """Handle "label" being False / '' and be defensive."""
            return Domain.AND([
                [(field_name, '=', value) if value or field_name != 'label' else ('label', 'in', (False, ''))]
                for field_name, value in field_values
            ])

        errors = set()
        for vals in vals_list:
            if 'url' not in vals:
                raise ValueError(_('Creating a Link Tracker without URL is not possible'))
            if vals['url'].startswith(('?', '#')):
                errors.add(_("“%s” is not a valid link, links cannot redirect to the current page.", vals['url']))
            vals['url'] = validate_url(vals['url'])
            # fill vals to use direct accessor in _format_key
            self._add_missing_default_values(vals)
            vals.update({key: False for key in LINK_TRACKER_UNIQUE_FIELDS if not vals.get(key)})
        if errors:
            raise UserError("\n".join(errors))

        # Find unique keys of trackers, then fetch existing trackers
        unique_keys = {_format_key(vals) for vals in vals_list}
        found_trackers = self.search(Domain.OR(_format_key_domain(key) for key in unique_keys))
        key_to_trackers_map = {_format_key(tracker): tracker for tracker in found_trackers}

        if len(unique_keys) != len(found_trackers):
            # Create trackers for values with unique keys not found
            seen_keys = set(key_to_trackers_map.keys())
            new_trackers = self.create([
                vals for vals in vals_list
                if (key := _format_key(vals)) not in seen_keys and not seen_keys.add(key)
            ])
            key_to_trackers_map.update((_format_key(tracker), tracker) for tracker in new_trackers)

        # Build final recordset following input order
        return self.browse([key_to_trackers_map[_format_key(vals)].id for vals in vals_list])