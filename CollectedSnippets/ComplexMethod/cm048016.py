def _compute_service_info(self):
        for wizard in self:
            message = ''
            if wizard.account_peppol_proxy_state == 'receiver':
                supported_doctypes = self.env['res.company']._peppol_supported_document_types()
                if (non_configurable := [
                    identifier
                    for identifier in (wizard.service_json or {})
                    if identifier not in supported_doctypes
                ]):
                    message = Markup('%s<ul>%s</ul>') % (
                        _(
                            "The following services are listed on your participant but cannot be configured here. "
                            "If you wish to configure them differently, please contact support."
                        ),
                        Markup().join(
                            Markup('<li>%s</li>') % (wizard.service_json[identifier]['document_name'])
                            for identifier in non_configurable
                        ),
                    )
            wizard.service_info = message