def write(self, vals):
        self.check_access('write')
        if vals.get('res_model') or vals.get('res_id'):
            model_and_ids = defaultdict(OrderedSet)
            if 'res_model' in vals and 'res_id' in vals:
                model_and_ids[vals['res_model']].add(vals['res_id'])
            else:
                for record in self:
                    model_and_ids[vals.get('res_model', record.res_model)].add(vals.get('res_id', record.res_id))
            if any(self._inaccessible_comodel_records(model_and_ids, 'write')):
                raise AccessError(_("Sorry, you are not allowed to access this document."))
        # remove computed field depending of datas
        for field in ('file_size', 'checksum', 'store_fname'):
            vals.pop(field, False)
        if 'mimetype' in vals or 'datas' in vals or 'raw' in vals:
            vals = self._check_contents(vals)
        res = super().write(vals)
        if 'url' in vals or 'type' in vals:
            self._check_serving_attachments()
        return res