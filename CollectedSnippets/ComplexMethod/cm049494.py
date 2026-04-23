def _snailmail_create(self, route):
        """
        Create a dictionnary object to send to snailmail server.

        :return: Dict in the form:
        {
            account_token: string,    //IAP Account token of the user
            documents: [{
                pages: int,
                pdf_bin: pdf file
                res_id: int (client-side res_id),
                res_model: char (client-side res_model),
                address: {
                    name: char,
                    street: char,
                    street2: char (OPTIONAL),
                    zip: int,
                    city: char,
                    state: char (state code (OPTIONAL)),
                    country_code: char (country code)
                }
                return_address: {
                    name: char,
                    street: char,
                    street2: char (OPTIONAL),
                    zip: int,
                    city: char,at
                    state: char (state code (OPTIONAL)),
                    country_code: char (country code)
                }
            }],
            options: {
                color: boolean (true if color, false if black-white),
                duplex: boolean (true if duplex, false otherwise),
                currency_name: char
            }
        }
        """
        account_token = self.env['iap.account'].sudo().get('snailmail').account_token
        dbuuid = self.env['ir.config_parameter'].sudo().get_param('database.uuid')
        documents = []

        for letter in self:
            recipient_name = letter.partner_id.name or letter.partner_id.parent_id and letter.partner_id.parent_id.name
            if not recipient_name:
                letter.write({
                    'info_msg': _('Invalid recipient name.'),
                    'state': 'error',
                    'error_code': 'MISSING_REQUIRED_FIELDS'
                    })
                continue
            document = {
                # generic informations to send
                'letter_id': letter.id,
                'res_model': letter.model,
                'res_id': letter.res_id,
                'contact_address': letter.partner_id.with_context(snailmail_layout=True, show_address=True).display_name,
                'address': {
                    'name': recipient_name,
                    'street': letter.partner_id.street,
                    'street2': letter.partner_id.street2,
                    'zip': letter.partner_id.zip,
                    'state': letter.partner_id.state_id.code if letter.partner_id.state_id else False,
                    'city': letter.partner_id.city,
                    'country_code': letter.partner_id.country_id.code
                },
                'return_address': {
                    'name': letter.company_id.partner_id.name,
                    'street': letter.company_id.partner_id.street,
                    'street2': letter.company_id.partner_id.street2,
                    'zip': letter.company_id.partner_id.zip,
                    'state': letter.company_id.partner_id.state_id.code if letter.company_id.partner_id.state_id else False,
                    'city': letter.company_id.partner_id.city,
                    'country_code': letter.company_id.partner_id.country_id.code,
                }
            }
            # Specific to each case:
            # If we are estimating the price: 1 object = 1 page
            # If we are printing -> attach the pdf
            if route == 'estimate':
                document.update(pages=1)
            else:
                # adding the web logo from the company for future possible customization
                document.update({
                    'company_logo': letter.company_id.logo_web and letter.company_id.logo_web.decode('utf-8') or False,
                })
                attachment = letter._fetch_attachment()
                if attachment:
                    document.update({
                        'pdf_bin': route == 'print' and attachment.datas.decode('utf-8'),
                        'pages': route == 'estimate' and self._count_pages_pdf(base64.b64decode(attachment.datas)),
                    })
                else:
                    letter.write({
                        'info_msg': 'The attachment could not be generated.',
                        'state': 'error',
                        'error_code': 'ATTACHMENT_ERROR'
                    })
                    continue
                if letter.company_id.external_report_layout_id == self.env.ref('l10n_de.external_layout_din5008', False):
                    document.update({
                        'rightaddress': 0,
                    })
            documents.append(document)

        return {
            'account_token': account_token,
            'dbuuid': dbuuid,
            'documents': documents,
            'options': {
                'color': self and self[0].color,
                'cover': self and self[0].cover,
                'duplex': self and self[0].duplex,
                'currency_name': 'EUR',
            },
            # this will not raise the InsufficientCreditError which is the behaviour we want for now
            'batch': True,
        }