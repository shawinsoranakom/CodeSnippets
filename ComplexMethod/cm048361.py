def test_report_quantity_1(self):
        product_form = Form(self.env['product.product'])
        product_form.is_storable = True
        product_form.name = 'Product'
        product = product_form.save()

        warehouse = self.env['stock.warehouse'].search([], limit=1)
        stock = self.env['stock.location'].create({
            'name': 'New Stock',
            'usage': 'internal',
            'location_id': warehouse.view_location_id.id,
        })

        # Inventory Adjustement of 50.0 today.
        self.env['stock.quant'].with_context(inventory_mode=True).create({
            'product_id': product.id,
            'location_id': stock.id,
            'inventory_quantity': 50
        }).action_apply_inventory()
        self.env.flush_all()
        report_records_today = self.env['report.stock.quantity']._read_group(
            [('product_id', '=', product.id), ('date', '=', date.today())],
            [], ['product_qty:sum'])
        report_records_tomorrow = self.env['report.stock.quantity']._read_group(
            [('product_id', '=', product.id), ('date', '=', date.today() + timedelta(days=1))],
            [], ['product_qty:sum'])
        report_records_yesterday = self.env['report.stock.quantity']._read_group(
            [('product_id', '=', product.id), ('date', '=', date.today() - timedelta(days=1))],
            [], ['product_qty:sum'])
        self.assertEqual(report_records_today[0][0], 50.0)
        self.assertEqual(report_records_tomorrow[0][0], 50.0)
        self.assertEqual(report_records_yesterday[0][0], 0.0)

        # Delivery of 20.0 units tomorrow
        move_out = self.env['stock.move'].create({
            'date': datetime.now() + timedelta(days=1),
            'location_id': stock.id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
            'product_id': product.id,
            'product_uom': product.uom_id.id,
            'product_uom_qty': 20.0,
        })
        self.env.flush_all()
        report_records_tomorrow = self.env['report.stock.quantity']._read_group(
            [('product_id', '=', product.id), ('date', '=', date.today() + timedelta(days=1))],
            [], ['product_qty:sum'])
        self.assertEqual(report_records_tomorrow[0][0], 50.0)
        move_out._action_confirm()
        self.env.flush_all()
        report_records_tomorrow = self.env['report.stock.quantity']._read_group(
            [('product_id', '=', product.id), ('date', '=', date.today() + timedelta(days=1))],
            ['state'], ['product_qty:sum'])
        self.assertEqual(sum(product_qty for state, product_qty in report_records_tomorrow if state == 'forecast'), 30.0)
        self.assertEqual(sum(product_qty for state, product_qty in report_records_tomorrow if state == 'out'), -20.0)
        report_records_today = self.env['report.stock.quantity']._read_group(
            [('product_id', '=', product.id), ('date', '=', date.today())],
            ['state'], ['product_qty:sum'])
        self.assertEqual(sum(product_qty for state, product_qty in report_records_today if state == 'forecast'), 50.0)

        # Receipt of 10.0 units tomorrow
        move_in = self.env['stock.move'].create({
            'date': datetime.now() + timedelta(days=1),
            'location_id': self.env.ref('stock.stock_location_suppliers').id,
            'location_dest_id': stock.id,
            'product_id': product.id,
            'product_uom': product.uom_id.id,
            'product_uom_qty': 10.0,
        })
        move_in._action_confirm()
        self.env.flush_all()
        report_records_tomorrow = self.env['report.stock.quantity']._read_group(
            [('product_id', '=', product.id), ('date', '=', date.today() + timedelta(days=1))],
            ['state'], ['product_qty:sum'])
        self.assertEqual(sum(product_qty for state, product_qty in report_records_tomorrow if state == 'forecast'), 40.0)
        self.assertEqual(sum(product_qty for state, product_qty in report_records_tomorrow if state == 'out'), -20.0)
        self.assertEqual(sum(product_qty for state, product_qty in report_records_tomorrow if state == 'in'), 10.0)
        report_records_today = self.env['report.stock.quantity']._read_group(
            [('product_id', '=', product.id), ('date', '=', date.today())],
            ['state'], ['product_qty:sum'])
        self.assertEqual(sum(product_qty for state, product_qty in report_records_today if state == 'forecast'), 50.0)

        # Delivery of 20.0 units tomorrow
        move_out = self.env['stock.move'].create({
            'date': datetime.now() - timedelta(days=1),
            'location_id': stock.id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
            'product_id': product.id,
            'product_uom': product.uom_id.id,
            'product_uom_qty': 30.0,
        })
        move_out._action_confirm()
        self.env.flush_all()
        report_records_today = self.env['report.stock.quantity']._read_group(
            [('product_id', '=', product.id), ('date', '=', date.today())],
            ['state'], ['product_qty:sum'])
        report_records_tomorrow = self.env['report.stock.quantity']._read_group(
            [('product_id', '=', product.id), ('date', '=', date.today() + timedelta(days=1))],
            ['state'], ['product_qty:sum'])
        report_records_yesterday = self.env['report.stock.quantity']._read_group(
            [('product_id', '=', product.id), ('date', '=', date.today() - timedelta(days=1))],
            ['state'], ['product_qty:sum'])

        self.assertEqual(sum(product_qty for state, product_qty in report_records_yesterday if state == 'forecast'), -30.0)
        self.assertEqual(sum(product_qty for state, product_qty in report_records_yesterday if state == 'out'), -30.0)
        self.assertEqual(sum(product_qty for state, product_qty in report_records_yesterday if state == 'in'), 0.0)

        self.assertEqual(sum(product_qty for state, product_qty in report_records_today if state == 'forecast'), 20.0)
        self.assertEqual(sum(product_qty for state, product_qty in report_records_today if state == 'out'), 0.0)
        self.assertEqual(sum(product_qty for state, product_qty in report_records_today if state == 'in'), 0.0)

        self.assertEqual(sum(product_qty for state, product_qty in report_records_tomorrow if state == 'forecast'), 10.0)
        self.assertEqual(sum(product_qty for state, product_qty in report_records_tomorrow if state == 'out'), -20.0)
        self.assertEqual(sum(product_qty for state, product_qty in report_records_tomorrow if state == 'in'), 10.0)