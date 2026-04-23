def _get_chart_template_data(self, template_code):
        template_data = defaultdict(lambda: defaultdict(dict))
        template_data['res.company']  # ensure it's the first property when iterating
        translatable_model_fields = self._get_translatable_template_model_fields()
        untranslatable_model_fields = self._get_untranslatable_fields_to_translate()
        for code in [None] + self._get_parent_template(template_code):
            for model, funcs in sorted(
                self._template_register[code].items(),
                key=lambda i: TEMPLATE_MODELS.index(i[0]) if i[0] in TEMPLATE_MODELS else 1000
            ):
                translatable_fields = translatable_model_fields.get(model, [])
                untranslatable_fields = untranslatable_model_fields.get(model, [])
                for func in funcs:
                    data = func(self, template_code)
                    if data is not None:
                        if model == 'template_data':
                            template_data[model].update(data)
                        else:
                            for xmlid, record in data.items():
                                # Store information about which module each field value originates from (for code translations).
                                # The final value of different fields may be determined by different functions.
                                # The last function to modify the record may not modify all or any of the translatable fields.
                                for field in translatable_fields + untranslatable_fields:
                                    if field in record:
                                        record.setdefault('__translation_module__', {})[field] = func._module

                                template_data[model][xmlid].update(record)
        return template_data