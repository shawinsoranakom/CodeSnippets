def test_20_bom_report(self):
        """ Simulate a crumble receipt with mrp and open the bom structure
        report and check that data insde are correct.
        """
        uom_kg = self.env.ref('uom.product_uom_kgm')
        uom_litre = self.env.ref('uom.product_uom_litre')
        crumble = self.env['product.product'].create({
            'name': 'Crumble',
            'is_storable': True,
            'uom_id': uom_kg.id,
        })
        butter = self.env['product.product'].create({
            'name': 'Butter',
            'is_storable': True,
            'uom_id': uom_kg.id,
            'standard_price': 7.01
        })
        biscuit = self.env['product.product'].create({
            'name': 'Biscuit',
            'is_storable': True,
            'uom_id': uom_kg.id,
            'standard_price': 1.5
        })
        bom_form_crumble = Form(self.env['mrp.bom'])
        bom_form_crumble.product_tmpl_id = crumble.product_tmpl_id
        bom_form_crumble.product_qty = 11
        bom_form_crumble.product_uom_id = uom_kg
        bom_crumble = bom_form_crumble.save()

        workcenter = self.env['mrp.workcenter'].create({
            'costs_hour': 10,
            'name': 'Deserts Table'
        })

        bom_crumble.write({
            'bom_line_ids': [
                Command.create({
                    'product_id': butter.id,
                    'product_uom_id': uom_kg.id,
                    'product_qty': 5,
                }),
                Command.create({
                    'product_id': biscuit.id,
                    'product_uom_id': uom_kg.id,
                    'product_qty': 6,
            })],
            'operation_ids': [
                Command.create({
                    'workcenter_id': workcenter.id,
                    'name': 'Prepare biscuits',
                    'time_cycle_manual': 5 * bom_crumble.product_qty,
                }),
                Command.create({
                    'workcenter_id': workcenter.id,
                    'name': 'Prepare butter',
                    'time_cycle_manual': 3 * bom_crumble.product_qty,
                }),
                Command.create({
                    'workcenter_id': workcenter.id,
                    'name': 'Mix manually',
                    'time_cycle_manual': 5 * bom_crumble.product_qty,
            })]
        })

        # TEST BOM STRUCTURE VALUE WITH BOM QUANTITY
        report_values = self.env['report.mrp.report_bom_structure']._get_report_data(bom_id=bom_crumble.id, searchQty=11, searchVariant=False)
        # 5 min 'Prepare biscuits' + 3 min 'Prepare butter' + 5 min 'Mix manually' = 13 minutes for 1 biscuits so 13 * 11 = 143 minutes
        self.assertEqual(report_values['lines']['operations_time'], 143.0, 'Operation time should be the same for 1 unit or for the batch')
        # Operation cost is the sum of operation line.
        self.assertEqual(float_compare(report_values['lines']['operations_cost'], 23.84, precision_digits=2), 0, '143 minute for 10$/hours -> 23.84')

        for component_line in report_values['lines']['components']:
            # standard price * bom line quantity * current quantity / bom finished product quantity
            if component_line['product'].id == butter.id:
                # 5 kg of butter at 7.01$ for 11kg of crumble -> 35.05$
                self.assertEqual(float_compare(component_line['bom_cost'], (7.01 * 5), precision_digits=2), 0)
            if component_line['product'].id == biscuit.id:
                # 6 kg of biscuits at 1.50$ for 11kg of crumble -> 9$
                self.assertEqual(float_compare(component_line['bom_cost'], (1.5 * 6), precision_digits=2), 0)
        # total price = 35.05 + 9 + operation_cost(23.84) = 67.89
        self.assertEqual(float_compare(report_values['lines']['bom_cost'], 67.89, precision_digits=2), 0, 'Product Bom Price is not correct')
        self.assertEqual(float_compare(report_values['lines']['bom_cost'] / 11.0, 6.17, precision_digits=2), 0, 'Product Unit Bom Price is not correct')

        # TEST BOM STRUCTURE VALUE BY UNIT
        report_values = self.env['report.mrp.report_bom_structure']._get_report_data(bom_id=bom_crumble.id, searchQty=1, searchVariant=False)
        # 5 min 'Prepare biscuits' + 3 min 'Prepare butter' + 5 min 'Mix manually' = 13 minutes
        self.assertEqual(report_values['lines']['operations_time'], 143.0, 'Operation time should be the same for 1 unit or for the batch')
        # Operation cost is the sum of operation line.
        operation_cost = float_round(bom_crumble.product_qty * 5 / 60 * 10, precision_digits=2) * 2 + float_round(bom_crumble.product_qty * 3 / 60 * 10, precision_digits=2)
        self.assertEqual(float_compare(report_values['lines']['operations_cost'], operation_cost, precision_digits=2), 0, '13 minute for 10$/hours -> 2.16')

        for component_line in report_values['lines']['components']:
            # standard price * bom line quantity * current quantity / bom finished product quantity
            if component_line['product'].id == butter.id:
                # 5 kg of butter at 7.01$ for 11kg of crumble -> / 11 for price per unit (3.19)
                self.assertEqual(float_compare(component_line['bom_cost'], (7.01 * 5) * (1 / 11), precision_digits=2), 0)
            if component_line['product'].id == biscuit.id:
                # 6 kg of biscuits at 1.50$ for 11kg of crumble -> / 11 for price per unit (0.82)
                self.assertEqual(float_compare(component_line['bom_cost'], (1.5 * 6) * (1 / 11), precision_digits=2), 0)
        # total price = 3.19 + 0.82 + operation_cost(23.84) = 27.85
        self.assertEqual(float_compare(report_values['lines']['bom_cost'], 27.85, precision_digits=2), 0, 'Bom Price is not correct')

        # TEST OPERATION COST WHEN PRODUCED QTY > BOM QUANTITY
        report_values_12 = self.env['report.mrp.report_bom_structure']._get_report_data(bom_id=bom_crumble.id, searchQty=12, searchVariant=False)
        report_values_22 = self.env['report.mrp.report_bom_structure']._get_report_data(bom_id=bom_crumble.id, searchQty=22, searchVariant=False)

        #Operation cost = 47.66 € = 256 (min) * 10€/h
        self.assertEqual(float_compare(report_values_22['lines']['operations_cost'], 47.66, precision_digits=2), 0, 'Operation cost is not correct')

        # Create a more complex BoM with a sub product
        cheese_cake = self.env['product.product'].create({
            'name': 'Cheese Cake 300g',
            'is_storable': True,
        })
        cream = self.env['product.product'].create({
            'name': 'cream',
            'is_storable': True,
            'uom_id': uom_litre.id,
            'standard_price': 5.17,
        })
        bom_form_cheese_cake = Form(self.env['mrp.bom'])
        bom_form_cheese_cake.product_tmpl_id = cheese_cake.product_tmpl_id
        bom_form_cheese_cake.product_qty = 60
        bom_form_cheese_cake.product_uom_id = self.uom_unit
        bom_cheese_cake = bom_form_cheese_cake.save()

        workcenter_2 = self.env['mrp.workcenter'].create({
            'name': 'cake mounting',
            'costs_hour': 20,
            'time_start': 10,
            'time_stop': 15
        })

        self.env['mrp.workcenter.capacity'].create({
            'workcenter_id': workcenter_2.id,
            'product_id': cheese_cake.id,
            'product_uom_id': cheese_cake.uom_id.id,
            'capacity': bom_cheese_cake.product_qty,
            'time_start': 12,
            'time_stop': 16,
        })

        bom_cheese_cake.write({
            'bom_line_ids': [
                Command.create({
                    'product_id': cream.id,
                    'product_uom_id': uom_litre.id,
                    'product_qty': 3,
                }),
                Command.create({
                    'product_id': crumble.id,
                    'product_uom_id': uom_kg.id,
                    'product_qty': 5.4,
            })],
            'operation_ids': [
                Command.create({
                    'workcenter_id': workcenter.id,
                    'name': 'Mix cheese and crumble',
                    'time_cycle_manual': 10 * bom_cheese_cake.product_qty,
                }),
                Command.create({
                    'workcenter_id': workcenter_2.id,
                    'name': 'Cake mounting',
                    'time_cycle_manual': 5 * bom_cheese_cake.product_qty,
            })]
        })

        # TEST CHEESE BOM STRUCTURE VALUE WITH BOM QUANTITY
        report_values = self.env['report.mrp.report_bom_structure']._get_report_data(bom_id=bom_cheese_cake.id, searchQty=60, searchVariant=False)
        # Operation time = 15 min * 60 + capacity_time_start + capacity_time_stop = 928
        self.assertEqual(report_values['lines']['operations_time'], 928.0, 'Operation time should be the same for 1 unit or for the batch')
        # Operation cost is the sum of operation line : (60 * 10)/60 * 10€ + (10 + 15 + 60 * 5)/60 * 20€ + (1 + 2)/60 * 20€ = 209,33€
        self.assertEqual(float_compare(report_values['lines']['operations_cost'], 209.33, precision_digits=2), 0)

        for component_line in report_values['lines']['components']:
            # standard price * bom line quantity * current quantity / bom finished product quantity
            if component_line['product'].id == cream.id:
                # 3 liter of cream at 5.17$ for 60 unit of cheese cake -> 15.51$
                self.assertEqual(float_compare(component_line['bom_cost'], (3 * 5.17), precision_digits=2), 0)
            if component_line['product'].id == crumble.id:
                # 5.4 kg of crumble at the cost of a batch.
                crumble_cost = self.env['report.mrp.report_bom_structure']._get_report_data(bom_id=bom_crumble.id, searchQty=5.4, searchVariant=False)['lines']['bom_cost']
                self.assertEqual(float_compare(component_line['bom_cost'], crumble_cost, precision_digits=2), 0)
        # total price = Cream (15.51€) + crumble_cost (45.47 €) + operation_cost(209,33) = 270.31€
        self.assertEqual(float_compare(report_values['lines']['bom_cost'], 270.31, precision_digits=2), 0, 'Product Bom Price is not correct')