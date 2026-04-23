def fn(record, log):
            converted = {}
            import_file_context = self.env.context.get('import_file')
            for field, value in record.items():
                if field in REFERENCING_FIELDS:
                    continue
                if not value:
                    converted[field] = False
                    continue
                try:
                    converted[field], ws = converters[field](value)
                    for w in ws:
                        if isinstance(w, str):
                            # wrap warning string in an ImportWarning for
                            # uniform handling
                            w = ImportWarning(w)
                        log(field, w)
                except (UnicodeEncodeError, UnicodeDecodeError) as e:
                    log(field, ValueError(str(e)))
                except ValueError as e:
                    if import_file_context:
                        # if the error is linked to a matching error, the error is a tuple
                        # E.g.:("Value X cannot be found for field Y at row 1", {
                        #   'more_info': {},
                        #   'value': 'X',
                        #   'field': 'Y',
                        #   'field_path': child_id/Y,
                        # })
                        # In order to link the error to the correct header-field couple in the import UI, we need to add
                        # the field path to the additional error info.
                        # As we raise the deepest child in error, we need to add the field path only for the deepest
                        # error in the import recursion. (if field_path is given, don't overwrite it)
                        error_info = len(e.args) > 1 and e.args[1]
                        if error_info and not error_info.get('field_path'):  # only raise the deepest child in error
                            error_info['field_path'] = self._get_import_field_path(field, value)
                    log(field, e)
            return converted