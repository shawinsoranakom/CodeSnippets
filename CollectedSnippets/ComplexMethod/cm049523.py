def _check_nemhandel_participant_exists(self, participant_info, edi_identification):
        service_href = ''
        if isinstance(participant_info, dict):
            participant_identifier = participant_info.get('identifier', '')
            if services := participant_info.get('services', []):
                service_href = services[0].get('href', '')
        else:
            # DEPRECATED: we now use Odoo peppol API to fetch participant info and get a json response
            # keeping this branch for compatibility
            participant_identifier = participant_info.findtext('{*}ParticipantIdentifier') or ''
            service_metadata = participant_info.find('.//{*}ServiceMetadataReference')
            if service_metadata is not None:
                service_href = service_metadata.attrib.get('href', '')

        nemhandel_user = self.env.company.sudo().nemhandel_edi_user
        edi_mode = nemhandel_user and nemhandel_user.edi_mode or self.env['ir.config_parameter'].sudo().get_param('l10n_dk_nemhandel.edi.mode')
        smp_nemhandel_url = 'smp-demo.nemhandel.dk' if edi_mode == 'test' else 'smp.nemhandel.dk'

        return edi_identification.lower() == participant_identifier.lower() and parse.urlsplit(service_href).netloc == smp_nemhandel_url