def _create_invoice(cls, move_type='out_invoice', invoice_date=None, date=None, post=False, **invoice_args):
        """
        This method quickly generates an ``account.move`` record with some quality of life helpers.
        These quality of life helpers are:

        - if `invoice_date`/`date` is filled but not the other, autofill the other date fields
        - if no `date` or `invoice_date` is passed, set the `invoice_date` to today by default
        - allow passing record immediately instead of getting the id / creating [Command.set(...)] everytime for one2many/many2many fields
        - allow passing None value in `invoice_args`, they will be filtered out before calling the move `create` method

        :param post: if True, the invoice will be posted
        :param invoice_args: additional overrides on the `account.move` `create` call
        :return: the created ``account.move`` record
        """
        # QoL: if `invoice_date`/`date` is filled but not the other, autofill the other date fields
        if move_type in cls.env['account.move'].get_invoice_types():
            if invoice_date and not date:
                date = invoice_date
            elif date and not invoice_date:
                invoice_date = date
            elif not date and not invoice_date:
                invoice_date = fields.Date.today()

        invoice_args |= {'date': date, 'invoice_date': invoice_date}

        # QoL: allow passing record immediately instead of getting the id / creating [Command.set(...)] everytime
        # QoL: delete all keys with None value from invoice_args
        cls._prepare_record_kwargs('account.move', invoice_args)

        invoice = cls.env['account.move'].create([{
            'move_type': move_type,
            'partner_id': cls.partner_a.id,
            'invoice_line_ids': [  # default invoice_line_ids
                cls._prepare_invoice_line(product_id=cls.product_a),
                cls._prepare_invoice_line(product_id=cls.product_b),
            ],
            **invoice_args,
        }])

        if post:
            invoice.action_post()

        cls.env.flush_all()
        return invoice