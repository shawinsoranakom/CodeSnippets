def _load(self, template_code, company, install_demo, force_create=True ):
        """Install this chart of accounts for the current company.

        :param template_code: code of the chart template to be loaded.
        :param company: the company we try to load the chart template on.
            If not provided, it is retrieved from the context.
        :param install_demo: whether or not we should load demo data right after loading the
            chart template.
        """
        # Ensure that the context is the correct one, even if not called by try_loading
        if not self.env.is_system():
            raise AccessError(_("Only administrators can install chart templates"))
        self = self.sudo()  # noqa: PLW0642
        chart_template_mapping = self._get_chart_template_mapping()[template_code]
        if not company.country_id:
            company.country_id = chart_template_mapping.get('country_id')

        module_name = chart_template_mapping.get('module')
        module = self.env['ir.module.module'].search([('name', '=', module_name), ('state', '=', 'uninstalled')])
        if module:
            module.button_immediate_install()
            self.env.transaction.reset()  # clear the transaction with an old registry
            self = self.env()['account.chart.template']  # noqa: PLW0642 create a new env with the new registry
        # To be able to use code translation we load everything in 'en_US'
        # The demo data is still loaded "normally" since code translations cannot be used for them reliably.
        # (Since we rely on the "@template functions" to determine the module to take the code translations from.)
        original_context_lang = self.env.context.get('lang')
        self = self.with_context(
            default_company_id=company.id,
            allowed_company_ids=[company.id],
            tracking_disable=True,
            delay_account_group_sync=True,
            lang='en_US',
            chart_template_load=True,
        )
        company = self.env['res.company'].browse(company.id)  # also update company.pool

        reload_template = template_code == company.chart_template
        company.chart_template = template_code

        if not reload_template and (not company.root_id._existing_accounting() or install_demo):
            children_companies = self.env['res.company'].search([('id', 'child_of', company.id)])
            for model in ('account.move',) + TEMPLATE_MODELS[::-1]:
                if not company.parent_id:
                    company_field = 'company_id' if 'company_id' in self.env[model] else 'company_ids'
                    records = self.env[model].sudo().with_context(active_test=False).search([(company_field, 'child_of', company.id)])
                    if company_field == 'company_ids':
                        records_to_keep = records.filtered(lambda r: r.company_ids - children_companies)
                        records -= records_to_keep
                        for records_for_companies in records_to_keep.grouped('company_ids').values():
                            records_for_companies.company_ids -= children_companies
                    records.with_context({MODULE_UNINSTALL_FLAG: True}).unlink()

        data = self._get_chart_template_data(template_code)
        template_data = data.pop('template_data')
        if company.parent_id:
            data = {
                'res.company': data['res.company'],
            }

        if reload_template:
            self._pre_reload_data(company, template_data, data, force_create)
            install_demo = False
        data = self._pre_load_data(template_code, company, template_data, data)
        self._load_data(data)
        self._post_load_data(template_code, company, template_data)
        self._load_translations(companies=company)

        # Manual sync because disable above (delay_account_group_sync)
        AccountGroup = self.env['account.group'].with_context(delay_account_group_sync=False)
        AccountGroup._adapt_parent_account_group(company=company)

        # Install the demo data when the first localization is instanciated on the company
        if install_demo and not reload_template:
            try:
                with self.env.cr.savepoint():
                    self = self.with_context(lang=original_context_lang)
                    self._install_demo(company.with_env(self.env))
            except Exception:
                # Do not rollback installation of CoA if demo data failed
                _logger.exception('Error while loading accounting demo data')
        for subsidiary in company.child_ids:
            self._load(template_code, subsidiary, install_demo, force_create)