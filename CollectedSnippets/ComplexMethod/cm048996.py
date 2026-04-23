def _post_to_web_service(self, values):
        self.ensure_one()

        error = self._check_can_post(values)
        if error:
            return error

        if not self.xml_attachment_id:
            self._generate_xml(values)

        if (
            not self.chain_index
            and not self.is_cancel
            and values['is_sale']
        ):
            # Assign unique 'chain index' from dedicated sequence
            self.sudo().chain_index = self.company_id._get_l10n_es_tbai_next_chain_index()

        try:
            # Call the web service, retrieve and parse response
            success, response_msgs = self._post_to_agency(self.env, values['is_sale'])
        except (RequestException) as e:
            # In case of timeout / request exception
            self.sudo().response_message = e
            return

        self.sudo().response_message = '\n'.join(response_msgs)
        if success:
            self.sudo().state = 'accepted'
        else:
            self.sudo().state = 'rejected'
            self.sudo().chain_index = 0