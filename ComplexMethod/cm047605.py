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