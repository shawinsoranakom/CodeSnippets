def _create_test_invoices_like_demo(cls, use_current_date=True):
        """ Create in the unit tests the same invoices created in demo data """
        payment_term = cls.env.ref("account.account_payment_term_end_following_month")
        incoterm = cls.env.ref("account.incoterm_EXW")

        decimal_price = cls.env.ref('product.decimal_price')
        decimal_price.digits = 4

        test_invoices_map = {
            'test_invoice_1': {
                "ref": "test_invoice_1: Invoice to gritti support service, vat 21",
                "partner_id": cls.res_partner_gritti_mono,
                "invoice_payment_term_id": payment_term,
                "move_type": "out_invoice",
                "invoice_date": "2021-03-01",
                "company_id": cls.company_ri,
                "invoice_line_ids": [
                    cls._prepare_invoice_line(product_id=cls.service_iva_21),
                ],
            },
            'test_invoice_2': {
                "ref": "test_invoice_2: Invoice to Servicios Globales with vat 21, 27 and 10,5",
                "partner_id": cls.res_partner_servicios_globales,
                "invoice_payment_term_id": payment_term,
                "move_type": "out_invoice",
                "invoice_date": "2021-03-05",
                "company_id": cls.company_ri,
                "invoice_line_ids": [
                    cls._prepare_invoice_line(product_id=cls.product_iva_105, price_unit=642.0, quantity=5),
                    cls._prepare_invoice_line(product_id=cls.service_iva_27, price_unit=250.0, quantity=1),
                    cls._prepare_invoice_line(product_id=cls.product_iva_105_perc, price_unit=3245.0, quantity=2),
                ],
            },
            'test_invoice_3': {
                "ref": "test_invoice_3: Invoice to ADHOC with vat cero and 21",
                "partner_id": cls.res_partner_adhoc,
                "invoice_payment_term_id": payment_term,
                "move_type": 'out_invoice',
                "invoice_date": "2021-03-01",
                "company_id": cls.company_ri,
                "invoice_line_ids": [
                    cls._prepare_invoice_line(product_id=cls.product_iva_105, price_unit=642.0, quantity=5),
                    cls._prepare_invoice_line(product_id=cls.product_iva_cero, price_unit=200.0, quantity=1),
                ],
            },
            'test_invoice_4': {
                'ref': 'test_invoice_4: Invoice to ADHOC with vat exempt and 21',
                "partner_id": cls.res_partner_adhoc,
                "invoice_payment_term_id": payment_term,
                "move_type": 'out_invoice',
                "invoice_date": "2021-03-01",
                "company_id": cls.company_ri,
                "invoice_line_ids": [
                    cls._prepare_invoice_line(product_id=cls.product_iva_105, price_unit=642.1234, quantity=5),
                    cls._prepare_invoice_line(product_id=cls.product_iva_exento, price_unit=100.5678, quantity=1),
                ],
            },
            'test_invoice_5': {
                'ref': 'test_invoice_5: Invoice to ADHOC with all type of taxes',
                "partner_id": cls.res_partner_adhoc,
                "invoice_payment_term_id": payment_term,
                "move_type": 'out_invoice',
                "invoice_date": "2021-03-13",
                "company_id": cls.company_ri,
                "invoice_line_ids": cls._get_ar_multi_invoice_line_ids(),
            },
            'test_invoice_6': {
                'ref': 'test_invoice_6: Invoice to Montana Sur, fiscal position changes taxes to exempt',
                "partner_id": cls.res_partner_montana_sur,
                "journal_id": cls.sale_expo_journal_ri,
                "invoice_payment_term_id": payment_term,
                "move_type": 'out_invoice',
                "invoice_date": "2021-03-03",
                "company_id": cls.company_ri,
                "invoice_incoterm_id": incoterm,
                "invoice_line_ids": cls._get_ar_multi_invoice_line_ids(),
            },
            'test_invoice_7': {
                'ref': 'test_invoice_7: Export invoice to Barcelona food, fiscal position changes tax to exempt (type 4 because it have services)',
                "partner_id": cls.res_partner_barcelona_food,
                "journal_id": cls.sale_expo_journal_ri,
                "invoice_payment_term_id": payment_term,
                "move_type": 'out_invoice',
                "invoice_date": "2021-03-03",
                "company_id": cls.company_ri,
                "invoice_incoterm_id": incoterm,
                "invoice_line_ids": cls._get_ar_multi_invoice_line_ids(),
            },
            'test_invoice_8': {
                'ref': 'test_invoice_8: Invoice to consumidor final',
                "partner_id": cls.partner_cf,
                "invoice_payment_term_id": payment_term,
                "move_type": 'out_invoice',
                "invoice_date": "2021-03-13",
                "company_id": cls.company_ri,
                "invoice_line_ids": [
                    cls._prepare_invoice_line(product_id=cls.service_iva_21, price_unit=642.0, quantity=1),
                ],
            },
            'test_invoice_10': {
                'ref': 'test_invoice_10; Invoice to ADHOC in USD and vat 21',
                "partner_id": cls.res_partner_adhoc,
                "invoice_payment_term_id": payment_term,
                "move_type": 'out_invoice',
                "invoice_date": "2021-03-13",
                "company_id": cls.company_ri,
                "invoice_line_ids": [
                    cls._prepare_invoice_line(product_id=cls.product_iva_105, price_unit=1000.0, quantity=5),
                ],
                "currency_id": cls.env.ref("base.USD"),
            },
            'test_invoice_11': {
                'ref': 'test_invoice_11: Invoice to ADHOC with many lines in order to prove rounding error, with 4 decimals of precision for the currency and 2 decimals for the product the error apperar',
                "partner_id": cls.res_partner_adhoc,
                "invoice_payment_term_id": payment_term,
                "move_type": 'out_invoice',
                "invoice_date": "2021-03-13",
                "company_id": cls.company_ri,
                "invoice_line_ids": [
                    cls._prepare_invoice_line(product_id=cls.service_iva_21, price_unit=1.12, quantity=1, name='Support Services 1'),
                    cls._prepare_invoice_line(product_id=cls.service_iva_21, price_unit=1.12, quantity=1, name='Support Services 2'),
                    cls._prepare_invoice_line(product_id=cls.service_iva_21, price_unit=1.12, quantity=1, name='Support Services 3'),
                    cls._prepare_invoice_line(product_id=cls.service_iva_21, price_unit=1.12, quantity=1, name='Support Services 4'),
                ],
            },
            'test_invoice_12': {
                'ref': 'test_invoice_12: Invoice to ADHOC with many lines in order to test rounding error, it is required to use a 4 decimal precision in prodct in order to the error occur',
                "partner_id": cls.res_partner_adhoc,
                "invoice_payment_term_id": payment_term,
                "move_type": 'out_invoice',
                "invoice_date": "2021-03-13",
                "company_id": cls.company_ri,
                "invoice_line_ids": [
                    cls._prepare_invoice_line(product_id=cls.service_iva_21, price_unit=15.7076, quantity=1, name='Support Services 1'),
                    cls._prepare_invoice_line(product_id=cls.service_iva_21, price_unit=5.3076, quantity=2, name='Support Services 2'),
                    cls._prepare_invoice_line(product_id=cls.service_iva_21, price_unit=3.5384, quantity=2, name='Support Services 3'),
                    cls._prepare_invoice_line(product_id=cls.service_iva_21, price_unit=1.6376, quantity=2, name='Support Services 4'),
                ],
            },
            'test_invoice_13': {
                'ref': 'test_invoice_13: Invoice to ADHOC with many lines in order to test zero amount invoices y rounding error. it is required to set the product decimal precision to 4 and change 260.59 for 260.60 in order to reproduce the error',
                "partner_id": cls.res_partner_adhoc,
                "invoice_payment_term_id": payment_term,
                "move_type": 'out_invoice',
                "invoice_date": "2021-03-13",
                "company_id": cls.company_ri,
                "invoice_line_ids": [
                    cls._prepare_invoice_line(product_id=cls.service_iva_21, price_unit=24.3, quantity=3, name='Support Services 1'),
                    cls._prepare_invoice_line(product_id=cls.service_iva_21, price_unit=260.59, quantity=1, name='Support Services 2'),
                    cls._prepare_invoice_line(product_id=cls.service_iva_21, price_unit=48.72, quantity=1, name='Support Services 3'),
                    cls._prepare_invoice_line(product_id=cls.service_iva_21, price_unit=13.666, quantity=1, name='Support Services 4'),
                    cls._prepare_invoice_line(product_id=cls.service_iva_21, price_unit=11.329, quantity=2, name='Support Services 5'),
                    cls._prepare_invoice_line(product_id=cls.service_iva_21, price_unit=68.9408, quantity=1, name='Support Services 6'),
                    cls._prepare_invoice_line(product_id=cls.service_iva_21, price_unit=4.7881, quantity=2, name='Support Services 7'),
                    cls._prepare_invoice_line(product_id=cls.service_iva_21, price_unit=12.0625, quantity=2, name='Support Services 8'),
                ],
            },
            'test_invoice_14': {
                'ref': 'test_invoice_14: Export invoice to Barcelona food, fiscal position changes tax to exempt (type 1 because only products)',
                "partner_id": cls.res_partner_barcelona_food,
                "journal_id": cls.sale_expo_journal_ri,
                "invoice_payment_term_id": payment_term,
                "move_type": 'out_invoice',
                "invoice_date": "2021-03-20",
                "company_id": cls.company_ri,
                "invoice_incoterm_id": incoterm,
                "invoice_line_ids": [
                    cls._prepare_invoice_line(product_id=cls.product_iva_105, price_unit=642.0, quantity=5),
                ],
            },
            'test_invoice_15': {
                'ref': 'test_invoice_15: Export invoice to Barcelona food, fiscal position changes tax to exempt (type 2 because only service)',
                "partner_id": cls.res_partner_barcelona_food,
                "journal_id": cls.sale_expo_journal_ri,
                "invoice_payment_term_id": payment_term,
                "move_type": 'out_invoice',
                "invoice_date": "2021-03-20",
                "company_id": cls.company_ri,
                "invoice_incoterm_id": incoterm,
                "invoice_line_ids": [
                    cls._prepare_invoice_line(product_id=cls.service_iva_27, price_unit=250.0, quantity=1),
                ],
            },
            'test_invoice_16': {
                'ref': 'test_invoice_16: Export invoice to Barcelona food, fiscal position changes tax to exempt (type 1 because it have products only, used to test refund of expo)',
                "partner_id": cls.res_partner_barcelona_food,
                "journal_id": cls.sale_expo_journal_ri,
                "invoice_payment_term_id": payment_term,
                "move_type": 'out_invoice',
                "invoice_date": "2021-03-22",
                "company_id": cls.company_ri,
                "invoice_incoterm_id": incoterm,
                "invoice_line_ids": [
                    cls._prepare_invoice_line(product_id=cls.product_iva_105, price_unit=642.0, quantity=5),
                ],
            },
            'test_invoice_17': {
                'ref': 'test_invoice_17: Invoice to ADHOC with 100%% of discount',
                "partner_id": cls.res_partner_adhoc,
                "invoice_payment_term_id": payment_term,
                "move_type": 'out_invoice',
                "invoice_date": "2021-03-13",
                "company_id": cls.company_ri,
                "invoice_line_ids": [
                    cls._prepare_invoice_line(product_id=cls.service_iva_21, price_unit=24.3, quantity=3, name='Support Services 8', discount=100),
                ],
            },
            'test_invoice_18': {
                'ref': 'test_invoice_18: Invoice to ADHOC with 100%% of discount and with different VAT aliquots',
                "partner_id": cls.res_partner_adhoc,
                "invoice_payment_term_id": payment_term,
                "move_type": 'out_invoice',
                "invoice_date": "2021-03-13",
                "company_id": cls.company_ri,
                "invoice_line_ids": [
                    cls._prepare_invoice_line(product_id=cls.service_iva_21, price_unit=24.3, quantity=3, name='Support Services 8', discount=100),
                    cls._prepare_invoice_line(product_id=cls.service_iva_27, price_unit=250.0, quantity=1, discount=100),
                    cls._prepare_invoice_line(product_id=cls.product_iva_105_perc, price_unit=3245.0, quantity=1),
                ],
            },
            'test_invoice_19': {
                'ref': 'test_invoice_19: Invoice to ADHOC with multiple taxes and perceptions',
                "partner_id": cls.res_partner_adhoc,
                "invoice_payment_term_id": payment_term,
                "move_type": 'out_invoice',
                "invoice_date": "2021-03-13",
                "company_id": cls.company_ri,
                "invoice_line_ids": [
                    cls._prepare_invoice_line(product_id=cls.service_iva_21, price_unit=24.3, quantity=3, name='Support Services 8'),
                    cls._prepare_invoice_line(product_id=cls.service_iva_27, price_unit=250.0, quantity=1),
                    cls._prepare_invoice_line(product_id=cls.product_iva_105_perc, price_unit=3245.0, quantity=1),
                ],
            }
        }

        if use_current_date:
            for invoice_key, invoice_values in test_invoices_map.items():
                invoice_values.pop('invoice_date')
                cls.demo_invoices[invoice_key] = cls._create_invoice_ar(**invoice_values)
        else:
            for key, values in test_invoices_map.items():
                values['invoice_line_ids'] = [line_data for _, _, line_data in values['invoice_line_ids']]
                with Form(cls.env['account.move'].with_context(default_move_type=values['move_type'])) as invoice_form:
                    invoice_form.ref = values['ref']
                    invoice_form.partner_id = values['partner_id']
                    invoice_form.invoice_payment_term_id = values['invoice_payment_term_id']
                    invoice_form.invoice_date = values['invoice_date']
                    if values.get('invoice_incoterm_id'):
                        invoice_form.invoice_incoterm_id = values['invoice_incoterm_id']
                    for line in values['invoice_line_ids']:
                        with invoice_form.invoice_line_ids.new() as line_form:
                            line_form.product_id = cls.env['product.product'].browse(line.get('product_id'))
                            line_form.price_unit = line.get('price_unit')
                            line_form.quantity = line.get('quantity')
                            if line.get('tax_ids'):
                                line_form.tax_ids = cls.env['account.tax'].browse(line.get('tax_ids'))
                            line_form.name = 'xxxx'
                            line_form.account_id = cls.company_data['default_account_revenue']
                cls.demo_invoices[key] = invoice_form.save()