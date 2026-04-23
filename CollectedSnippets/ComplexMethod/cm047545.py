def __ensure_xml_id(self, skip=False):
        """ Create missing external ids for records in ``self``, and return an
            iterator of pairs ``(record, xmlid)`` for the records in ``self``.

        :rtype: Iterable[Model, str | None]
        """
        if skip:
            return ((record, None) for record in self)

        if not self:
            return iter([])

        if not self._is_an_ordinary_table():
            raise Exception(
                "You can not export the column ID of model %s, because the "
                "table %s is not an ordinary table."
                % (self._name, self._table))

        modname = '__export__'

        cr = self.env.cr
        cr.execute(SQL("""
            SELECT res_id, module, name
            FROM ir_model_data
            WHERE model = %s AND res_id IN %s
        """, self._name, tuple(self.ids)))
        xids = {
            res_id: (module, name)
            for res_id, module, name in cr.fetchall()
        }
        def to_xid(record_id):
            (module, name) = xids[record_id]
            return ('%s.%s' % (module, name)) if module else name

        # create missing xml ids
        missing = self.filtered(lambda r: r.id not in xids)
        if not missing:
            return (
                (record, to_xid(record.id))
                for record in self
            )

        xids.update(
            (r.id, (modname, '%s_%s_%s' % (
                r._table,
                r.id,
                uuid.uuid4().hex[:8],
            )))
            for r in missing
        )
        fields = ['module', 'model', 'name', 'res_id']

        # disable eventual async callback / support for the extent of
        # the COPY FROM, as these are apparently incompatible
        callback = psycopg2.extensions.get_wait_callback()
        psycopg2.extensions.set_wait_callback(None)
        try:
            cr.copy_from(io.StringIO(
                u'\n'.join(
                    u"%s\t%s\t%s\t%d" % (
                        modname,
                        record._name,
                        xids[record.id][1],
                        record.id,
                    )
                    for record in missing
                )),
                table='ir_model_data',
                columns=fields,
            )
        finally:
            psycopg2.extensions.set_wait_callback(callback)
        self.env['ir.model.data'].invalidate_model(fields)

        return (
            (record, to_xid(record.id))
            for record in self
        )