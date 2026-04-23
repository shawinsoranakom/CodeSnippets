def _generate_primary_page_templates(self):
        """ Generates page templates based on manifest entries. """
        View = self.env['ir.ui.view']
        manifest = Manifest.for_addon(self.name)
        templates = manifest['new_page_templates']

        # TODO Find a way to create theme and other module's template patches
        # Create or update template views per group x key
        create_values = []
        for group in templates:
            for template_name in templates[group]:
                xmlid = f'{self.name}.new_page_template_sections_{group}_{template_name}'
                wrapper = f'%s.new_page_template_{group}_{template_name}_%s'
                calls = '\n    '.join([
                    f'''<t t-snippet-call="{wrapper % (snippet_key.split('.') if '.' in snippet_key else ('website', snippet_key))}"/>'''
                    for snippet_key in templates[group][template_name]
                ])
                create_values.append({
                    'name': f"New page template: {template_name!r} in {group!r}",
                    'type': 'qweb',
                    'key': xmlid,
                    'arch': f'<div id="wrap">\n    {calls}\n</div>',
                })
        keys = [values['key'] for values in create_values]
        existing_primary_templates = View.search_read([('mode', '=', 'primary'), ('key', 'in', keys)], ['key'])
        existing_primary_template_keys = {data['key']: data['id'] for data in existing_primary_templates}
        missing_create_values = []
        update_count = 0
        for create_value in create_values:
            if create_value['key'] in existing_primary_template_keys:
                View.browse(existing_primary_template_keys[create_value['key']]).with_context(no_cow=True).write({
                    'arch': create_value['arch'],
                })
                update_count += 1
            else:
                missing_create_values.append(create_value)
        if missing_create_values:
            missing_records = View.create(missing_create_values)
            self._create_model_data(missing_records)
            _logger.info('Generated %s primary page templates for %r', len(missing_create_values), self.name)
        if update_count:
            _logger.info('Updated %s primary page templates for %r', update_count, self.name)