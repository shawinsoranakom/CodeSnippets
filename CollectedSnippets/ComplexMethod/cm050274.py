def fetch(self, field_names=None):
        if self.browse().has_access('read'):
            return super().fetch(field_names)

        # HACK: retrieve publicly available values from hr.employee.public and
        # copy them to the cache of self; non-public data will be missing from
        # cache, and interpreted as an access error
        if field_names is None:
            field_names = [field.name for field in self._determine_fields_to_fetch()]
        field_names = [f_name for f_name in field_names if f_name != 'current_version_id']
        self._check_private_fields(field_names)
        self.flush_recordset(field_names)
        public = self.env['hr.employee.public'].browse(self._ids)
        public.fetch(field_names)
        # make sure all related fields from employee are in cache
        for field_name in field_names:
            public_field = self.env['hr.employee.public']._fields[field_name]
            private_field = self.env['hr.employee']._fields[field_name]
            if (public_field.related and public_field.related_field.model_name == 'hr.employee'
                    or private_field.inherited and private_field.inherited_field.model_name == 'hr.version'):
                public.mapped(field_name)
        self._copy_cache_from(public, field_names)