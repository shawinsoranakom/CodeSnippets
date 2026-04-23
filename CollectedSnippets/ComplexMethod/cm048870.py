def test_15_anglo_saxon_variant_price_unit(self):
        """
        Test the price unit of a variant from which template has another variant with kit bom.
        Products:
            Template A
                variant NOKIT
                variant KIT:
                    Component A
        Business Flow:
            create products and kit
            create SO selling both variants
            validate the delivery
            create the invoice
            post the invoice
        """

        # Create environment
        self.env.company.currency_id = self.env.ref('base.USD')
        self.env.company.anglo_saxon_accounting = True
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.category = self.env.ref('product.product_category_goods').copy({
            'name': 'Test category',
            'property_valuation': 'real_time',
            'property_cost_method': 'fifo',
        })
        self.stock_location = self.company_data['default_warehouse'].lot_stock_id

        # Create variant attributes
        self.prod_att_test = self.env['product.attribute'].create({'name': 'test'})
        self.prod_attr_KIT = self.env['product.attribute.value'].create({'name': 'KIT', 'attribute_id': self.prod_att_test.id, 'sequence': 1})
        self.prod_attr_NOKIT = self.env['product.attribute.value'].create({'name': 'NOKIT', 'attribute_id': self.prod_att_test.id, 'sequence': 2})

        # Create the template
        self.product_template = self.env['product.template'].create({
            'name': 'Template A',
            'is_storable': True,
            'uom_id': self.uom_unit.id,
            'invoice_policy': 'delivery',
            'categ_id': self.category.id,
            'attribute_line_ids': [(0, 0, {
                'attribute_id': self.prod_att_test.id,
                'value_ids': [(6, 0, [self.prod_attr_KIT.id, self.prod_attr_NOKIT.id])]
            })]
        })

        # Create the variants
        self.pt_attr_KIT = self.product_template.attribute_line_ids[0].product_template_value_ids[0]
        self.pt_attr_NOKIT = self.product_template.attribute_line_ids[0].product_template_value_ids[1]
        self.variant_KIT = self.product_template._get_variant_for_combination(self.pt_attr_KIT)
        self.variant_NOKIT = self.product_template._get_variant_for_combination(self.pt_attr_NOKIT)
        # Assign a cost to the NOKIT variant
        self.variant_NOKIT.write({'standard_price': 25})

        # Create the components
        self.comp_kit_a = self.env['product.product'].create({
            'name': 'Component Kit A',
            'is_storable': True,
            'uom_id': self.uom_unit.id,
            'categ_id': self.category.id,
            'standard_price': 20
        })
        self.comp_kit_b = self.env['product.product'].create({
            'name': 'Component Kit B',
            'is_storable': True,
            'uom_id': self.uom_unit.id,
            'categ_id': self.category.id,
            'standard_price': 10
        })

        # Create the bom
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_template.id,
            'product_id': self.variant_KIT.id,
            'product_qty': 1.0,
            'type': 'phantom'
        })
        self.env['mrp.bom.line'].create({
            'product_id': self.comp_kit_a.id,
            'product_qty': 2.0,
            'bom_id': bom.id
        })
        self.env['mrp.bom.line'].create({
            'product_id': self.comp_kit_b.id,
            'product_qty': 1.0,
            'bom_id': bom.id
        })

        # Create the quants
        self.env['stock.quant']._update_available_quantity(self.comp_kit_a, self.stock_location, 2)
        self.env['stock.quant']._update_available_quantity(self.comp_kit_b, self.stock_location, 1)
        self.env['stock.quant']._update_available_quantity(self.variant_NOKIT, self.stock_location, 1)

        # Create the sale order
        so_vals = {
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
            'order_line': [(0, 0, {
                'name': self.variant_KIT.name,
                'product_id': self.variant_KIT.id,
                'product_uom_qty': 1,
                'price_unit': 100,
            }), (0, 0, {
                'name': self.variant_NOKIT.name,
                'product_id': self.variant_NOKIT.id,
                'product_uom_qty': 1,
                'price_unit': 50
            })],
            'company_id': self.env.company.id
        }
        so = self.env['sale.order'].create(so_vals)
        # Validate the sale order
        so.action_confirm()
        # Deliver the products
        pick = so.picking_ids
        pick.button_validate()
        # Create the invoice
        so._create_invoices()
        # Validate the invoice
        invoice = so.invoice_ids
        invoice.action_post()

        amls = invoice.line_ids
        aml_kit_expense = amls.filtered(lambda l: l.display_type == 'cogs' and l.debit > 0 and l.product_id == self.variant_KIT)
        aml_kit_output = amls.filtered(lambda l: l.display_type == 'cogs' and l.credit > 0 and l.product_id == self.variant_KIT)
        aml_nokit_expense = amls.filtered(lambda l: l.display_type == 'cogs' and l.debit > 0 and l.product_id == self.variant_NOKIT)
        aml_nokit_output = amls.filtered(lambda l: l.display_type == 'cogs' and l.credit > 0 and l.product_id == self.variant_NOKIT)

        # Check that the Cost of Goods Sold for variant KIT is equal to 2*(2*20)+10 = 90
        self.assertEqual(aml_kit_expense.debit, 90, "Cost of Good Sold entry missing or mismatching for variant with kit")
        self.assertEqual(aml_kit_output.credit, 90, "Cost of Good Sold entry missing or mismatching for variant with kit")
        # Check that the Cost of Goods Sold for variant NOKIT is equal to its standard_price = 25
        self.assertEqual(aml_nokit_expense.debit, 25, "Cost of Good Sold entry missing or mismatching for variant without kit")
        self.assertEqual(aml_nokit_output.credit, 25, "Cost of Good Sold entry missing or mismatching for variant without kit")