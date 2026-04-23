def testUnit(mo_tmpl, serialTrigger=None):
            mo = self.create_mo(mo_tmpl, 1)
            mo.action_confirm()

            #  are partially reserved (stock.move state is partially_available)
            mo.action_assign()
            for mov in mo.move_raw_ids:
                if mov.has_tracking == "none":
                    self.assertEqual(raw_none_qty, mov.quantity, "Reserved quantity shall be equal to " + str(raw_none_qty) + ".")
                else:
                    self.assertEqual(raw_tracked_qty, mov.quantity, "Reserved quantity shall be equal to " + str(raw_tracked_qty) + ".")

            if serialTrigger is None:
                self.executeConsumptionTriggers(mo)
            elif serialTrigger == 1:
                mo.qty_producing = 1
                mo._set_qty_producing(False)
            elif serialTrigger == 2:
                mo.action_generate_serial()

            for mov in mo.move_raw_ids:
                if mov.has_tracking == "none":
                    self.assertTrue(mov.picked, "non tracked components should be picked")
                else:
                    self.assertEqual(mov.product_qty, mov.quantity, "Done quantity shall be equal to To Consume quantity.")
            mo.action_cancel()