def write(self, vals):
        """
            Override to correctly upgrade themes after upgrade/installation of modules.

            # Install

                If this theme wasn't installed before, then load it for every website
                for which it is in the stream.

                eg. The very first installation of a theme on a website will trigger this.

                eg. If a website uses theme_A and we install sale, then theme_A_sale will be
                    autoinstalled, and in this case we need to load theme_A_sale for the website.

            # Upgrade

                There are 2 cases to handle when upgrading a theme:

                * When clicking on the theme upgrade button on the interface,
                    in which case there will be an http request made.

                    -> We want to upgrade the current website only, not any other.

                * When upgrading with -u, in which case no request should be set.

                    -> We want to upgrade every website using this theme.
        """
        if request and request.db and request.env and request.env.context.get('apply_new_theme'):
            self = self.with_context(apply_new_theme=True)

        for module in self:
            if module.name.startswith('theme_') and vals.get('state') == 'installed':
                _logger.info('Module %s has been loaded as theme template (%s)' % (module.name, module.state))

                if module.state in ['to install', 'to upgrade']:
                    websites_to_update = module._theme_get_stream_website_ids()

                    if module.state == 'to upgrade' and request:
                        Website = self.env['website']
                        current_website = Website.get_current_website()
                        websites_to_update = current_website if current_website in websites_to_update else Website

                    for website in websites_to_update:
                        module._theme_load(website)

        return super(IrModuleModule, self).write(vals)