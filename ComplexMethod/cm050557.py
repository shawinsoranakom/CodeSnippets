def test_auto_email_send(self):
        with patch.object(fields.Datetime, 'now', return_value=self.monday_1pm) as _:
            with patch.object(fields.Date, 'today', return_value=self.monday_1pm.date()) as _:
                with patch.object(fields.Date, 'context_today', return_value=self.monday_1pm.date()) as _:
                    line_pizza = self.env['lunch.order'].create({
                        'product_id': self.product_pizza.id,
                        'date': self.monday_1pm.date(),
                        'supplier_id': self.supplier_pizza_inn.id,
                    })

                    line_pizza.action_order()
                    assert line_pizza.state == 'ordered'

                    self.supplier_pizza_inn._send_auto_email()

                    assert line_pizza.state == 'sent'

                    line_pizza_olive = self.env['lunch.order'].create({
                        'product_id': self.product_pizza.id,
                        'topping_ids_1': [(6, 0, [self.topping_olives.id])],
                        'date': self.monday_1pm.date(),
                        'supplier_id': self.supplier_pizza_inn.id,
                    })
                    line_tuna = self.env['lunch.order'].create({
                        'product_id': self.product_sandwich_tuna.id,
                        'date': self.monday_1pm.date(),
                        'supplier_id': self.supplier_coin_gourmand.id,
                    })

                    (line_pizza_olive | line_tuna).action_order()
                    assert line_pizza_olive.state == 'ordered'
                    assert line_tuna.state == 'ordered'

                    self.supplier_pizza_inn._send_auto_email()

                    assert line_pizza_olive.state == 'sent'
                    assert line_tuna.state == 'ordered'

                    line_pizza_2 = self.env['lunch.order'].create({
                        'product_id': self.product_pizza.id,
                        'quantity': 2,
                        'date': self.monday_1pm.date(),
                        'supplier_id': self.supplier_pizza_inn.id,
                    })

                    line_pizza_olive_2 = self.env['lunch.order'].create({
                        'product_id': self.product_pizza.id,
                        'topping_ids_1': [(6, 0, [self.topping_olives.id])],
                        'date': self.monday_1pm.date(),
                        'supplier_id': self.supplier_pizza_inn.id,
                    })

                    line_tuna_2 = self.env['lunch.order'].create({
                        'product_id': self.product_sandwich_tuna.id,
                        'quantity': 2,
                        'date': self.monday_1pm.date(),
                        'supplier_id': self.supplier_coin_gourmand.id,
                    })

                    ######################################################
                    # id:  # lines:               # state:      # quantity:
                    #######################################################
                    # 1    # line_pizza           # sent        # 1
                    # 2    # line_pizza_olive     # sent        # 1
                    # 3    # line_tuna            # ordered     # 1
                    # 4    # line_pizza_2         # new         # 2
                    # 5    # line_pizza_olive_2   # new         # 1
                    # 6    # line_tuna_2          # new         # 2

                    (line_pizza_2 | line_pizza_olive_2 | line_tuna_2).action_order()

                    ######################################################
                    # id:  # lines:               # state:      # quantity:
                    #######################################################
                    # 1    # line_pizza           # sent        # 1
                    # 2    # line_pizza_olive     # sent        # 1
                    # 3    # line_tuna            # ordered     # 3 (1 + 2 from line_tuna_2 id=6)
                    # 4    # line_pizza_2         # ordered     # 2
                    # 5    # line_pizza_olive_2   # ordered     # 1

                    assert all(line.state == 'ordered' for line in [line_pizza_2, line_pizza_olive_2])

                    self.assertEqual(line_tuna_2.active, False)
                    self.assertEqual(line_tuna.quantity, 3)

                    self.supplier_pizza_inn._send_auto_email()