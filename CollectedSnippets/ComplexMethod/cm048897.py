def _get_qr_vals(self, qr_method, amount, currency, debtor_partner, free_communication, structured_communication):
        """ Getting content for the QR through calling QRIS API and storing the QRIS transaction as a record"""
        # EXTENDS account
        if qr_method == "id_qr":
            model = self.env.context.get('qris_model')
            model_id = self.env.context.get('qris_model_id')

            # qris_trx is to help us fetch the backend record associated to the model and model_id.
            # we are using model and model_id instead of model.browse(id) because while executing this method
            # not all backend records are created already. For example, pos.order record isn't created until
            # payment is completed on the PoS interace.
            qris_trx = self.env['l10n_id.qris.transaction']._get_latest_transaction(model, model_id)

            # QRIS codes are valid for 30 minutes. To leave some margin, we will return the same QR code we already
            # generated if the invoice is re-accessed before 25m. Otherwise, a new QR code is generated
            # Additionally, we want to check that it's requesting for the same amount as it's possible to change
            # amount in apps like PoS.
            if qris_trx and qris_trx.qris_amount == int(amount):
                now = fields.Datetime.now()
                latest_qr_date = qris_trx.qris_creation_datetime

                if (now - latest_qr_date).total_seconds() < 1500:
                    return qris_trx['qris_content']

            params = {
                "do": "create-invoice",
                "apikey": self.sudo().l10n_id_qris_api_key,
                "mID": self.sudo().l10n_id_qris_mid,
                "cliTrxNumber": free_communication or structured_communication,
                "cliTrxAmount": int(amount)
            }
            response = _l10n_id_make_qris_request('show_qris.php', params)
            if response.get("status") == "failed":
                raise ValidationError(response.get("data"))
            data = response.get('data')

            # create a new transaction line while also converting the qris_request_date to UTC time
            if model and model_id:
                new_trx = self.env['l10n_id.qris.transaction'].create({
                    'model': model,
                    'model_id': model_id,
                    'qris_invoice_id': data.get('qris_invoiceid'),
                    'qris_amount': int(amount),
                    # Since the QRIS response is always returned with "Asia/Jakarta" timezone which is UTC+07:00
                    'qris_creation_datetime': fields.Datetime.to_datetime(data.get('qris_request_date')) - datetime.timedelta(hours=7),
                    'qris_content': data.get('qris_content'),
                    'bank_id': self.id
                })

                # Search the backend record and attach the qris transaction to the record if it exists.
                trx_record = new_trx._get_record()
                if trx_record:
                    trx_record.l10n_id_qris_transaction_ids |= new_trx

            return data.get('qris_content')

        return super()._get_qr_vals(qr_method, amount, currency, debtor_partner, free_communication, structured_communication)