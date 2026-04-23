def _generate_xml(self, values):
        self.ensure_one()

        def format_float(value, precision_digits=2):
            rounded_value = float_round(value, precision_digits=precision_digits)
            return float_repr(rounded_value, precision_digits=precision_digits)

        values.update({
            'doc': self,
            **self._get_header_values(),
            **self._get_sender_values(),
            **(self._get_recipient_values(values['partner'], values["is_simplified"]) if values['partner'] and not self.is_cancel or not values['is_sale'] else {}),
            'datetime_now': datetime.now(tz=timezone('Europe/Madrid')),
            'format_date': lambda d: datetime.strftime(d, '%d-%m-%Y'),
            'format_time': lambda d: datetime.strftime(d, '%H:%M:%S'),
            'format_float': format_float,
        })

        xml_doc = None

        if values['is_sale']:
            values.update({
                'is_emission': not self.is_cancel,
                **self.company_id._get_l10n_es_tbai_license_dict(),
                **(self._get_sale_values(values) if not self.is_cancel else {}),
            })
            xml_doc = self._generate_sale_document_xml(values)

        elif self.company_id.l10n_es_tbai_tax_agency == 'bizkaia':
            company = self.company_id
            freelancer = company._l10n_es_freelancer()
            values.update({'freelancer': freelancer})
            xml_doc = self._generate_purchase_document_xml_bi(values)

        if xml_doc is not None:
            self.sudo().xml_attachment_id = self.env['ir.attachment'].create({
                'name': values['attachment_name'],
                'raw': etree.tostring(xml_doc, encoding='UTF-8'),
                'type': 'binary',
                'res_model': values['res_model'],
                'res_id': values['res_id'],
            })