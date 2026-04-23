def test_10_variants(self):
        test_bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_7_template.id,
            'product_uom_id': self.uom_unit.id,
            'product_qty': 4.0,
            'type': 'normal',
            'operation_ids': [
                Command.create({
                    'name': 'Cutting Machine',
                    'workcenter_id': self.workcenter_1.id,
                    'time_cycle': 12,
                    'sequence': 1
                }),
                Command.create({
                    'name': 'Weld Machine',
                    'workcenter_id': self.workcenter_1.id,
                    'time_cycle': 18,
                    'sequence': 2,
                    'bom_product_template_attribute_value_ids': [Command.link(self.product_7_attr1_v1.id)]
                }),
                Command.create({
                    'name': 'Taking a coffee',
                    'workcenter_id': self.workcenter_1.id,
                    'time_cycle': 5,
                    'sequence': 3,
                    'bom_product_template_attribute_value_ids': [Command.link(self.product_7_attr1_v2.id)]
                })
            ],
            'byproduct_ids': [
                Command.create({
                    'product_id': self.product_1.id,
                    'product_uom_id': self.product_1.uom_id.id,
                    'product_qty': 1,
                }),
                Command.create({
                    'product_id': self.product_2.id,
                    'product_uom_id': self.product_2.uom_id.id,
                    'product_qty': 1,
                    'bom_product_template_attribute_value_ids': [Command.link(self.product_7_attr1_v1.id)]
                }),
                Command.create({
                    'product_id': self.product_3.id,
                    'product_uom_id': self.product_3.uom_id.id,
                    'product_qty': 1,
                    'bom_product_template_attribute_value_ids': [Command.link(self.product_7_attr1_v2.id)]
                }),
            ],
            'bom_line_ids': [
                Command.create({
                    'product_id': self.product_2.id,
                    'product_qty': 2,
                }),
                Command.create({
                    'product_id': self.product_3.id,
                    'product_qty': 2,
                    'bom_product_template_attribute_value_ids': [Command.link(self.product_7_attr1_v1.id)],
                }),
                Command.create({
                    'product_id': self.product_4.id,
                    'product_qty': 2,
                    'bom_product_template_attribute_value_ids': [Command.link(self.product_7_attr1_v2.id)],
                }),
            ]
        })
        test_bom_l1, test_bom_l2, test_bom_l3 = test_bom.bom_line_ids
        boms, lines = test_bom.explode(self.product_7_3, 4)
        self.assertIn(test_bom, [b[0]for b in boms])
        self.assertIn(test_bom_l1, [l[0] for l in lines])
        self.assertNotIn(test_bom_l2, [l[0] for l in lines])
        self.assertNotIn(test_bom_l3, [l[0] for l in lines])

        boms, lines = test_bom.explode(self.product_7_1, 4)
        self.assertIn(test_bom, [b[0]for b in boms])
        self.assertIn(test_bom_l1, [l[0] for l in lines])
        self.assertIn(test_bom_l2, [l[0] for l in lines])
        self.assertNotIn(test_bom_l3, [l[0] for l in lines])

        boms, lines = test_bom.explode(self.product_7_2, 4)
        self.assertIn(test_bom, [b[0]for b in boms])
        self.assertIn(test_bom_l1, [l[0] for l in lines])
        self.assertNotIn(test_bom_l2, [l[0] for l in lines])
        self.assertIn(test_bom_l3, [l[0] for l in lines])

        mrp_order_form = Form(self.env['mrp.production'])
        mrp_order_form.product_id = self.product_7_3
        mrp_order = mrp_order_form.save()
        self.assertEqual(mrp_order.bom_id, test_bom)
        self.assertEqual(mrp_order.bom_id.operation_ids[0].time_total, 165)
        self.assertEqual(len(mrp_order.workorder_ids), 1)
        self.assertEqual(mrp_order.workorder_ids.operation_id, test_bom.operation_ids[0])
        self.assertEqual(len(mrp_order.move_byproduct_ids), 1)
        self.assertEqual(mrp_order.move_byproduct_ids.product_id, self.product_1)

        mrp_order_form = Form(self.env['mrp.production'])
        mrp_order_form.product_id = self.product_7_1
        mrp_order_form.product_id = self.env['product.product']  # Check form
        mrp_order_form.product_id = self.product_7_1
        mrp_order_form.bom_id = self.env['mrp.bom']  # Check form
        mrp_order_form.bom_id = test_bom
        mrp_order = mrp_order_form.save()
        self.assertEqual(mrp_order.bom_id, test_bom)
        self.assertEqual(len(mrp_order.workorder_ids), 2)
        self.assertEqual(mrp_order.workorder_ids.operation_id, test_bom.operation_ids[:2])
        self.assertEqual(len(mrp_order.move_byproduct_ids), 2)
        self.assertEqual(mrp_order.move_byproduct_ids.product_id, self.product_1 | self.product_2)

        mrp_order_form = Form(self.env['mrp.production'])
        mrp_order_form.product_id = self.product_7_2
        mrp_order = mrp_order_form.save()
        self.assertEqual(mrp_order.bom_id, test_bom)
        self.assertEqual(len(mrp_order.workorder_ids), 2)
        self.assertEqual(mrp_order.workorder_ids.operation_id, test_bom.operation_ids[0] | test_bom.operation_ids[2])
        self.assertEqual(len(mrp_order.move_byproduct_ids), 2)
        self.assertEqual(mrp_order.move_byproduct_ids.product_id, self.product_1 | self.product_3)