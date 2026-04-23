def _compute_account_templates(self):
        chart_category = self.env.ref('base.module_category_accounting_localizations_account_charts')
        ChartTemplate = self.env['account.chart.template']
        for module in self:
            templates = {}
            if module.category_id == chart_category or module.name == 'account':
                try:
                    python_module = import_module(f"odoo.addons.{module.name}.models")
                except ModuleNotFoundError:
                    templates = {}
                else:
                    templates = {
                        fct._l10n_template[0]: {
                            'name': template_values.get('name'),
                            'parent': template_values.get('parent'),
                            'sequence': template_values.get('sequence', 1),
                            'country': template_values.get('country', ''),
                            'visible': template_values.get('visible', True),
                            'installed': module.state == "installed",
                            'module': module.name,
                        }
                        for _name, mdl in getmembers(python_module, template_module)
                        for _name, cls in getmembers(mdl, template_class)
                        for _name, fct in getmembers(cls, template_function)
                        if (template_values := fct(ChartTemplate))
                    }

            module.account_templates = {
                code: templ(self.env, code, **vals)
                for code, vals in sorted(templates.items(), key=lambda kv: kv[1]['sequence'])
            }