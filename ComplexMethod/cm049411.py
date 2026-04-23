def create(self, vals_list):
        """Create the UTM sources if necessary, generate the name based on the content in batch."""
        # Create all required <utm.source>
        utm_sources = self.env['utm.source'].create([
            {
                'name': values.get('name')
                or self.env.context.get('default_name')
                or self.env['utm.source']._generate_name(self, values.get(self._rec_name)),
            }
            for values in vals_list
            if not values.get('source_id')
        ])

        # Update "vals_list" to add the ID of the newly created source
        vals_list_missing_source = [values for values in vals_list if not values.get('source_id')]
        for values, source in zip(vals_list_missing_source, utm_sources):
            values['source_id'] = source.id

        for values in vals_list:
            if 'name' in values:
                del values['name']

        return super().create(vals_list)