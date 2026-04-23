def execute_import(self, fields, columns, options, dryrun=False):
        """ Actual execution of the import

        :param fields: import mapping: maps each column to a field,
                       ``False`` for the columns to ignore
        :type fields: list(str|bool)
        :param columns: columns label
        :type columns: list(str|bool)
        :param dict options:
        :param bool dryrun: performs all import operations (and
                            validations) but rollbacks writes, allows
                            getting as much errors as possible without
                            the risk of clobbering the database.
        :returns: A list of errors. If the list is empty the import
                  executed fully and correctly. If the list is
                  non-empty it contains dicts with 3 keys:

                  ``type``
                    the type of error (``error|warning``)
                  ``message``
                    the error message associated with the error (a string)
                  ``record``
                    the data which failed to import (or ``false`` if that data
                    isn't available or provided)
        :rtype: dict(ids: list(int), messages: list({type, message, record}))
        """
        self.ensure_one()
        import_savepoint = self.env.cr.savepoint(flush=False)

        try:
            input_file_data, import_fields = self._convert_import_data(fields, options)
            # Parse date and float field
            input_file_data = self._parse_import_data(input_file_data, import_fields, options)
        except ImportValidationError as error:
            return {'messages': [error.__dict__]}

        _logger.info('importing %d rows...', len(input_file_data))

        binary_filenames = self._extract_binary_filenames(import_fields, input_file_data)

        import_fields, merged_data = self.with_context(import_options=options)._handle_multi_mapping(import_fields, input_file_data)

        if options.get('fallback_values'):
            merged_data = self._handle_fallback_values(import_fields, merged_data, options['fallback_values'])

        name_create_enabled_fields = options.pop('name_create_enabled_fields', {})
        import_limit = options.pop('limit', None)
        model = self.env[self.res_model].with_context(
            import_file=True,
            name_create_enabled_fields=name_create_enabled_fields,
            import_set_empty_fields=options.get('import_set_empty_fields', []),
            import_skip_records=options.get('import_skip_records', []),
            _import_limit=import_limit)
        import_result = model.load(import_fields, merged_data)
        _logger.info('done importing data into model: %s', model._name)

        # If transaction aborted, RELEASE SAVEPOINT is going to raise
        # an InternalError (ROLLBACK should work, maybe). Ignore that.
        with contextlib.suppress(psycopg2.InternalError):
            import_savepoint.close(rollback=dryrun)
        if dryrun:
            # cancel all changes done to the registry/ormcache
            # we need to clear the cache in case any created id was added to an ormcache and would be missing afterward
            self.pool.clear_all_caches()
            # don't propagate to other workers since it was rollbacked
            self.pool.reset_changes()
            _logger.info('Previous import was a dry/test run, changes were reset')

        # Insert/Update mapping columns when import complete successfully
        if import_result['ids'] and options.get('has_headers'):
            BaseImportMapping = self.env['base_import.mapping']
            for index, column_name in enumerate(columns):
                if column_name:
                    # Update to latest selected field
                    mapping_domain = [('res_model', '=', self.res_model), ('column_name', '=', column_name)]
                    column_mapping = BaseImportMapping.search(mapping_domain, limit=1)
                    if column_mapping:
                        if column_mapping.field_name != fields[index]:
                            column_mapping.field_name = fields[index]
                    else:
                        BaseImportMapping.create({
                            'res_model': self.res_model,
                            'column_name': column_name,
                            'field_name': fields[index]
                        })
        if 'name' in import_fields:
            index_of_name = import_fields.index('name')
            skipped = options.get('skip', 0)
            # pad front as data doesn't contain anythig for skipped lines
            r = import_result['name'] = [''] * skipped
            # only add names for the window being imported
            r.extend(self._stringify_date_like_objects(x[index_of_name], options) for x in input_file_data[:import_limit])
            # pad back (though that's probably not useful)
            r.extend([''] * (len(input_file_data) - (import_limit or 0)))
        else:
            import_result['name'] = []

        skip = options.get('skip', 0)
        # convert load's internal nextrow to the imported file's
        if import_result['nextrow']: # don't update if nextrow = 0 (= no nextrow)
            import_result['nextrow'] += skip
        if binary_filenames:
            import_result['binary_filenames'] = binary_filenames

        return import_result