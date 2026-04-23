def _load_translations(self, langs=None, companies=None, template_data=None):
        """Load the translations of the chart template.

        :param langs: the lang code to load the translations for. If one of the codes is not present,
                      we are looking for it more generic locale (i.e. `en` instead of `en_US`)
        :type langs: list[str]
        :param companies: the companies to load the translations for
        :type companies: Model<res.company>
        """
        langs = langs or [code for code, _name in self.env['res.lang'].get_installed()]
        available_template_codes = list(self._get_chart_template_mapping(get_all=True))
        companies = companies or self.env['res.company'].search([('chart_template', 'in', available_template_codes)])

        translation_importer = TranslationImporter(self.env.cr, verbose=False)

        # Gather translations for records that are created from the chart_template data
        for company in companies:
            chart_template_data = template_data or self.env['account.chart.template'] \
                .with_context(ignore_missing_tags=True) \
                .with_company(company) \
                .sudo() \
                ._get_chart_template_data(company.chart_template)
            chart_template_data.pop('template_data', None)
            for mname, data in chart_template_data.items():
                for _xml_id, record in data.items():
                    fnames = {fname.split('@')[0] for fname in record if fname != '__translation_module__'}
                    for lang in langs:
                        for fname in fnames:
                            field = self.env[mname]._fields.get(fname)
                            if not field or not field.translate:
                                continue
                            field_translation = self._get_field_translation(record, fname, lang)
                            if field_translation:
                                xml_id = _xml_id if '.' in _xml_id else self.company_xmlid(_xml_id, company)
                                translation_importer.model_translations[mname][fname][xml_id][lang] = field_translation

        # Gather translations for the TEMPLATE_MODELS records that are not created from the chart_template data
        translation_langs = [lang for lang in langs if lang != 'en_US']  # there are no code translations for 'en_US' (original language)
        for (mname, _xml_id, module, fields) in self._get_untranslated_translatable_template_model_records(translation_langs, companies):
            for (field, value) in fields.items():
                if not value or 'en_US' not in value:
                    continue
                value_en_US = value['en_US']
                xml_id = f"{module}.{_xml_id}"
                for lang in [lang for lang in translation_langs if lang not in value]:
                    if lang in translation_importer.model_translations[mname][field][xml_id]:
                        continue
                    value_translated = None
                    for code_module in ([module, 'account'] if module != 'account' else ['account']):
                        value_translated = get_python_translation(code_module, lang, value_en_US)
                        if not value_translated and (re.match(r"<div>.*</div>", value_en_US)):
                            # Manage HTML fields sanitized when no html tag was provided
                            value_translated = get_python_translation(code_module, lang, value_en_US[5:-6])
                            if value_translated:
                                value_translated = f"<div>{value_translated}</div>"
                        if value_translated:
                            translation_importer.model_translations[mname][field][xml_id][lang] = value_translated
                            break

        translation_importer.save(overwrite=False)