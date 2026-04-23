def write(self, vals):
        # Instanciate the first template of the module on the current company upon installing the module
        was_installed = len(self) == 1 and self.state in ('installed', 'to upgrade', 'to remove')
        res = super().write(vals)
        is_installed = len(self) == 1 and self.state == 'installed'
        if (
            not was_installed and is_installed
            and not self.env.company.chart_template
            and self.account_templates
            and (guessed := next((
                tname
                for tname, tvals in self.account_templates.items()
                if (self.env.company.country_id.id and tvals['country_id'] == self.env.company.country_id.id)
                or tname == 'generic_coa'
            ), None))
        ):
            def try_loading(env):
                env['account.chart.template'].try_loading(
                    guessed,
                    env.company,
                )
            self.env.registry._auto_install_template = try_loading
        return res