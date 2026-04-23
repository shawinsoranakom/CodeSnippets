def try_loading(self, template_code, company, install_demo=False, force_create=True):
        """Check if the chart template can be loaded then proceeds installing it.

        :param template_code: code of the chart template to be loaded.
        :type template_code: str
        :param company: the company we try to load the chart template on.
            If not provided, it is retrieved from the context.
        :type company: int, Model<res.company>
        :param install_demo: whether or not we should load demo data right after loading the
            chart template.
        :type install_demo: bool
        :param force_create: Determines the loading behavior. If True, forces the creation of new entries;
            if False, prevents new creations and performs updates on existing data where applicable.
        :type force_create: bool
        """
        if not company:
            return
        if not self.env.registry.loaded and not install_demo and not hasattr(self.env.registry, '_auto_install_template'):
            _logger.warning(
                'Incorrect usage of try_loading without a fully loaded registry. This could lead to issues. (%s-%s)',
                company.name,
                template_code
            )
        if isinstance(company, int):
            company = self.env['res.company'].browse([company])

        template_code = template_code or company and self._guess_chart_template(company.country_id)

        if template_code in {'syscohada', 'syscebnl'} and template_code != company.chart_template:
            raise UserError(_("The %s chart template shouldn't be selected directly. Instead, you should directly select the chart template related to your country.", template_code))

        return self._load(template_code, company, install_demo, force_create)