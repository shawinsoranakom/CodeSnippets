def create(self, vals_list):
        record_tuple_set = set()

        # remove computed field depending of datas
        vals_list = [{
            key: value
            for key, value
            in vals.items()
            if key not in ('file_size', 'checksum', 'store_fname')
        } for vals in vals_list]
        checksum_raw_map = {}

        for values in vals_list:
            # needs to be popped in all cases to bypass `_inverse_datas`
            datas = values.pop('datas', None)
            if raw := values.get('raw'):
                if isinstance(raw, str):
                    values['raw'] = raw.encode()
            elif datas:
                values['raw'] = base64.b64decode(datas)
            else:
                values['raw'] = b''

            values = self._check_contents(values)
            if raw := values.pop('raw'):
                values.update(self._get_datas_related_values(raw, values['mimetype']))
                checksum_raw_map[values['checksum']] = raw

            # 'check()' only uses res_model and res_id from values, and make an exists.
            # We can group the values by model, res_id to make only one query when
            # creating multiple attachments on a single record.
            record_tuple = (values.get('res_model'), values.get('res_id'))
            record_tuple_set.add(record_tuple)

        # don't use possible contextual recordset for check, see commit for details
        model_and_ids = defaultdict(set)
        for res_model, res_id in record_tuple_set:
            model_and_ids[res_model].add(res_id)
        if any(self._inaccessible_comodel_records(model_and_ids, 'write')):
            raise AccessError(_("Sorry, you are not allowed to access this document."))
        records = super().create(vals_list)
        if self._storage() != 'db':
            for checksum, raw in checksum_raw_map.items():
                self._file_write(raw, checksum)
        records._check_serving_attachments()
        return records