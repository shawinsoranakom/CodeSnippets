def _export_translatable_records(self, records, field_names):
        """ Export translations of all stored/inherited translated fields. Create external id if needed. """
        if not records:
            return

        fields = records._fields

        if records._inherits:
            inherited_fields = defaultdict(list)
            for field_name in field_names:
                field = records._fields[field_name]
                if field.translate and not field.store and field.inherited_field:
                    inherited_fields[field.inherited_field.model_name].append(field_name)
            for parent_mname, parent_fname in records._inherits.items():
                if parent_mname in inherited_fields:
                    self._export_translatable_records(records[parent_fname], inherited_fields[parent_mname])

        if not any(fields[field_name].translate and fields[field_name].store for field_name in field_names):
            return

        records._BaseModel__ensure_xml_id()

        model_name = records._name
        query = """SELECT min(concat(module, '.', name)), res_id
                             FROM ir_model_data
                            WHERE model = %s
                              AND res_id = ANY(%s)
                         GROUP BY model, res_id"""

        self._cr.execute(query, (model_name, records.ids))

        imd_per_id = {
            res_id: ImdInfo((tmp := module_xml_name.split('.', 1))[1], model_name, res_id, tmp[0])
            for module_xml_name, res_id in self._cr.fetchall()
        }

        self._export_imdinfo(model_name, imd_per_id)