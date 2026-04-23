def _export_translatable_records(self):
        """ Export translations of all translated records having an external id """
        modules = self._installed_modules if 'all' in self._modules else list(self._modules)
        xml_defined = set()
        for module in modules:
            for filepath in get_datafile_translation_path(module):
                fileformat = os.path.splitext(filepath)[-1][1:].lower()
                with file_open(filepath, mode='rb') as source:
                    for entry in translation_file_reader(source, fileformat=fileformat, module=module):
                        xml_defined.add((entry['imd_model'], module, entry['imd_name']))

        query = """SELECT min(name), model, res_id, module
                     FROM ir_model_data
                    WHERE module = ANY(%s)
                 GROUP BY model, res_id, module
                 ORDER BY module, model, min(name)"""

        self._cr.execute(query, (modules,))

        records_per_model = defaultdict(dict)
        for (imd_name, model, res_id, module) in self._cr.fetchall():
            if (model, module, imd_name) in xml_defined:
                continue
            records_per_model[model][res_id] = ImdInfo(imd_name, model, res_id, module)

        for model, imd_per_id in records_per_model.items():
            self._export_imdinfo(model, imd_per_id)