def load(self, fields, data):
        """
        Attempts to load the data matrix, and returns a list of ids (or
        ``False`` if there was an error and no id could be generated) and a
        list of messages.

        The ids are those of the records created and saved (in database), in
        the same order they were extracted from the file. They can be passed
        directly to :meth:`~read`

        :param fields: list of fields to import, at the same index as the corresponding data
        :type fields: list(str)
        :param data: row-major matrix of data to import
        :type data: list(list(str))
        :returns: {ids: list(int)|False, messages: [Message][, lastrow: int]}
        """
        from .fields_relational import One2many  # noqa: PLC0415

        # determine values of mode, current_module and noupdate
        mode = self.env.context.get('mode', 'init')
        current_module = self.env.context.get('module', '__import__')
        noupdate = self.env.context.get('noupdate', False)
        # add current module in context for the conversion of xml ids
        self = self.with_context(_import_current_module=current_module)

        cr = self.env.cr
        savepoint = cr.savepoint()

        fields = [fix_import_export_id_paths(f) for f in fields]

        ids = []
        messages = []

        # list of (xid, vals, info) for records to be created in batch
        batch = []
        batch_xml_ids = set()
        # models in which we may have created / modified data, therefore might
        # require flushing in order to name_search: the root model and any
        # o2m
        creatable_models = {self._name}
        for field_path in fields:
            if field_path[0] in (None, 'id', '.id'):
                continue
            model_fields = self._fields
            for field_name in field_path:
                if field_name in (None, 'id', '.id'):
                    break

                if isinstance(model_fields.get(field_name), One2many):
                    comodel = model_fields[field_name].comodel_name
                    creatable_models.add(comodel)
                    model_fields = self.env[comodel]._fields

        def flush(*, xml_id=None, model=None):
            if not batch:
                return

            assert not (xml_id and model), \
                "flush can specify *either* an external id or a model, not both"

            if xml_id and xml_id not in batch_xml_ids:
                if xml_id not in self.env:
                    return
            if model and model not in creatable_models:
                return

            data_list = [
                dict(xml_id=xid, values=vals, info=info, noupdate=noupdate)
                for xid, vals, info in batch
            ]
            batch.clear()
            batch_xml_ids.clear()

            # try to create in batch
            global_error_message = None
            try:
                with cr.savepoint():
                    recs = self._load_records(data_list, mode == 'update')
                    ids.extend(recs.ids)
                return
            except psycopg2.InternalError as e:
                # broken transaction, exit and hope the source error was already logged
                if not any(message['type'] == 'error' for message in messages):
                    info = data_list[0]['info']
                    messages.append(dict(info, type='error', message=_(u"Unknown database error: '%s'", e)))
                return
            except UserError as e:
                global_error_message = dict(data_list[0]['info'], type='error', message=str(e))
            except Exception:
                pass

            errors = 0
            # try again, this time record by record
            for i, rec_data in enumerate(data_list, 1):
                try:
                    rec = self._load_records([rec_data], mode == 'update')
                    cr.flush()  # make sure flush exceptions are raised here
                    ids.append(rec.id)
                except psycopg2.Warning as e:
                    savepoint.rollback()
                    info = rec_data['info']
                    messages.append(dict(info, type='warning', message=str(e)))
                except psycopg2.Error as e:
                    savepoint.rollback()
                    info = rec_data['info']
                    pg_error_info = {'message': self._sql_error_to_message(e)}
                    if e.diag.table_name == self._table:
                        e_fields = get_columns_from_sql_diagnostics(self.env.cr, e.diag, check_registry=True)
                        if len(e_fields) == 1:
                            pg_error_info['field'] = e_fields[0]
                    messages.append(dict(info, type='error', **pg_error_info))
                    # Failed to write, log to messages, rollback savepoint (to
                    # avoid broken transaction) and keep going
                    errors += 1
                except UserError as e:
                    savepoint.rollback()
                    info = rec_data['info']
                    messages.append(dict(info, type='error', message=str(e)))
                    errors += 1
                except Exception as e:  # noqa: BLE001
                    savepoint.rollback()
                    _logger.debug("Error while loading record", exc_info=True)
                    info = rec_data['info']
                    message = _('Unknown error during import: %(error_type)s: %(error_message)s', error_type=e.__class__, error_message=e)
                    moreinfo = _('Resolve other errors first')
                    messages.append(dict(info, type='error', message=message, moreinfo=moreinfo))
                    # Failed for some reason, perhaps due to invalid data supplied,
                    # rollback savepoint and keep going
                    errors += 1
                if errors >= 10 and (errors >= i / 10):
                    messages.append({
                        'type': 'warning',
                        'message': _("Found more than 10 errors and more than one error per 10 records, interrupted to avoid showing too many errors.")
                    })
                    break
            if errors > 0 and global_error_message and global_error_message not in messages:
                # If we cannot create the records 1 by 1, we display the error raised when we created the records simultaneously
                messages.insert(0, global_error_message)

        # make 'flush' available to the methods below, in the case where XMLID
        # resolution fails, for instance
        flush_recordset = self.with_context(import_flush=flush, import_cache=LRU(1024))

        # TODO: break load's API instead of smuggling via context?
        limit = self.env.context.get('_import_limit')
        if limit is None:
            limit = float('inf')
        extracted = flush_recordset._extract_records(fields, data, log=messages.append, limit=limit)

        converted = flush_recordset._convert_records(extracted, log=messages.append, savepoint=savepoint)

        info = {'rows': {'to': -1}}
        for id, xid, record, info in converted:
            if self.env.context.get('import_file') and self.env.context.get('import_skip_records'):
                if any([record.get(field) is None for field in self.env.context['import_skip_records']]):
                    continue
            if xid:
                xid = xid if '.' in xid else "%s.%s" % (current_module, xid)
                batch_xml_ids.add(xid)
            elif id:
                record['id'] = id
            batch.append((xid, record, info))

        flush()
        if any(message['type'] == 'error' for message in messages):
            savepoint.rollback()
            ids = False
            # cancel all changes done to the registry/ormcache
            self.pool.reset_changes()
        savepoint.close(rollback=False)

        nextrow = info['rows']['to'] + 1
        if nextrow < limit:
            nextrow = 0
        return {
            'ids': ids,
            'messages': messages,
            'nextrow': nextrow,
        }