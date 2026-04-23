def get_select_mask(self):
        """
        Convert the self.deferred_loading data structure to an alternate data
        structure, describing the field that *will* be loaded. This is used to
        compute the columns to select from the database and also by the
        QuerySet class to work out which fields are being initialized on each
        model. Models that have all their fields included aren't mentioned in
        the result, only those that have field restrictions in place.
        """
        field_names, defer = self.deferred_loading
        if not field_names:
            return {}
        mask = {}
        for field_name in field_names:
            part_mask = mask
            for part in field_name.split(LOOKUP_SEP):
                part_mask = part_mask.setdefault(part, {})
        opts = self.get_meta()
        if defer:
            return self._get_defer_select_mask(opts, mask)
        return self._get_only_select_mask(opts, mask)