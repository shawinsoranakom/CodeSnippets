def test_install_with_translations(self):
        """ Ensure that the translations are loaded correctly when installing chart data; i.e. test '_load_translations' and that the untranslatable fields are translated correctly.
        Note: The '_load_translations' function depends on the '_get_chart_template_data' function for some information.
        The result of '_get_chart_template_data' is mocked (correctly) in this test (and not tested).
        """

        # Local mock for '_get_chart_template_mapping'
        # We will use / install a dedicated new chart 'translation' (not just reload 'test')
        # To have control over the original / en_US values.
        def local_get_mapping(self, get_all=False):
            return {'translation': {
                'name': 'translation',
                'country_id': None,
                'country_code': None,
                'modules': ['account'],
                'parent': None,
            }}

        company = self.company

        # Create records that are not part of the chart template
        # They will be translated via code translations.
        # The module used to source the translation is the module from the xml_id or 'account' (as fallback)

        non_chart_data = {
            'account.group': {
                # try module 'no_translation'; fallback to 'account'
                'no_translation.test_chart_template_company_test_free_account_group': {
                    'name': 'Free Account Group',
                    'code_prefix_start': 333330,
                    'code_prefix_end': 333339,
                    'company_id': company.id,
                },
            },
            'account.account': {
                # translate via 'translation' module
                'translation.test_chart_template_company_test_free_account': {
                    'name': 'Free Account',
                    'code': '333331',
                    'account_type': 'asset_current',
                    'company_ids': [Command.link(company.id)],
                },
            },
            'account.tax': {
                # translate via 'translation' module;
                # 2 translatable fields ('name' and 'description')
                'translation.test_chart_template_company_test_free_tax': {
                    "name": "Free Tax",
                    "description": "Free Tax Description",
                    "amount": "0.00",
                    "company_id": company.id,
                },
            },
        }

        # Local function to "extend" '_post_load_data' to ensure the creation of the records from 'non_chart_data'
        def test_post_load_data(template_code, company, template_data):
            for model, data in non_chart_data.items():
                for xml_id, values in data.items():
                    self.env[model]._load_records([{
                        'xml_id': xml_id,
                        'values': values,
                    }])

        # Create a local mock of '_get_chart_template_data'; "extend" 'test_get_data' with the translation info

        translation_update_for_test_get_data = {
            # Use code translations from module 'translation'
            'account.journal': {
                'bank': {
                    'name': "Bank",
                    'code': "B",  # untranslatable field; shortened due to length restriction (for _translation)
                    '__translation_module__': {
                        'name': 'translation',
                        'code': 'translation',
                    },
                },
            },
            # Different modules for code translations of 'name' and 'description'
            'account.tax': {
                'test_tax_1_template': {
                    'name': "Tax 1",
                    'description': "Tax 1 Description",
                    '__translation_module__': {
                        'name': 'translation',
                        'description': 'translation2',
                    },
                },
            },
            # Use 'name@' and not code translation
            'account.tax.group': {
                'tax_group_taxes': {
                    'name': "Taxes",
                    'name@fr': "Taxes FR",
                    '__translation_module__': {
                        'name': 'translation',
                    },
                },
            },
        }

        def local_get_data(self, template_code):
            data = test_get_data(self, template_code)
            for model, record_info in translation_update_for_test_get_data.items():
                for xmlid, data_update in record_info.items():
                    data[model][xmlid].update(data_update)
            return data

        # Tranlations should fall back to more generic locale 'fr'

        # Target lang for untranslatable fields
        company.partner_id.lang = self.env['res.lang']._activate_lang('fr_BE').code

        # Init empty mock translations to make sure we do not use unintended translation
        mock_python_translations = {}

        for module, lang, value, translation in [
            # wrong translations
            ('translation', 'fr', "Taxes", "WRONG"),  # there is a value in the chart data
            ('translation', 'fr', "Free Account", "Free Account FR"),  # there is a value for fr_BE
            # correct translations
            ('translation', 'fr', "Bank", "Bank FR"),
            ('translation', 'fr', "B", "B FR"),
            ('translation', 'fr', "Tax 1", "Tax 1 FR"),
            ('translation', 'fr_BE', "Free Account", "Free Account FR_BE"),
            ('translation', 'fr', "Free Tax", "Free Tax FR"),
            ('translation', 'fr', "Free Tax Description", "Free Tax Description FR"),
            ('translation2', 'fr', "Tax 1 Description", "Tax 1 Description translation2/FR"),
            ('account', 'fr', "Free Account Group", "Free Account Group account/FR"),
        ]:
            mock_python_translations.setdefault((module, lang), {})[value] = translation

        with patch.object(AccountChartTemplate, '_get_chart_template_mapping', side_effect=local_get_mapping, autospec=True):
            with patch.object(AccountChartTemplate, '_get_chart_template_data', side_effect=local_get_data, autospec=True):
                with patch.object(AccountChartTemplate, '_post_load_data', wraps=test_post_load_data):
                    with patch.object(code_translations, 'python_translations', mock_python_translations):
                        self.env['account.chart.template'].try_loading('translation', company=company, install_demo=False)

        # Check translations
        translatable_model_fields = self.env['account.chart.template']._get_translatable_template_model_fields()
        untranslatable_model_fields = self.env['account.chart.template']._get_untranslatable_fields_to_translate()
        fields_to_translate = {
            model: set(translatable_model_fields.get(model, []) + untranslatable_model_fields.get(model, []))
            for model in TEMPLATE_MODELS
        }

        self.assertEqual({
            f'{xmlid}.{field}@{lang}': self.env['account.chart.template'].ref(xmlid).with_context(lang=lang)[field]
            for chart_like_data in [non_chart_data, translation_update_for_test_get_data]
            for model, data in chart_like_data.items()
            for xmlid, record_data in data.items()
            for field in record_data if field in fields_to_translate.get(model, set())
            for lang in ['en_US', 'fr_BE']
        }, {
            'bank.code@en_US': 'B FR',  # untranslatable field loaded in lang fr_BE
            'bank.code@fr_BE': 'B FR',
            'bank.name@en_US': 'Bank',
            'bank.name@fr_BE': 'Bank FR',
            'no_translation.test_chart_template_company_test_free_account_group.name@en_US': 'Free Account Group',
            'no_translation.test_chart_template_company_test_free_account_group.name@fr_BE': 'Free Account Group account/FR',  # fallback to account
            'tax_group_taxes.name@en_US': 'Taxes',
            'tax_group_taxes.name@fr_BE': 'Taxes FR',
            'test_tax_1_template.description@en_US': Markup('<div>Tax 1 Description</div>'),
            'test_tax_1_template.description@fr_BE': Markup('Tax 1 Description translation2/FR'),
            'test_tax_1_template.name@en_US': 'Tax 1',
            'test_tax_1_template.name@fr_BE': 'Tax 1 FR',
            'translation.test_chart_template_company_test_free_account.name@en_US': 'Free Account',
            'translation.test_chart_template_company_test_free_account.name@fr_BE': 'Free Account FR_BE',  # do not use generic lang
            'translation.test_chart_template_company_test_free_tax.description@en_US': Markup('<div>Free Tax Description</div>'),
            'translation.test_chart_template_company_test_free_tax.description@fr_BE': Markup('<div>Free Tax Description FR</div>'),
            'translation.test_chart_template_company_test_free_tax.name@en_US': 'Free Tax',
            'translation.test_chart_template_company_test_free_tax.name@fr_BE': 'Free Tax FR',
        })