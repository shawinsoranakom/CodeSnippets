def executeConsumptionTriggers(self, mrp_productions):
        """There's 3 different triggers to test : _onchange_producing(), action_generate_serial(), button_mark_done().

        Depending on the tracking of the final product and the availability of the components,
        only a part of these 3 triggers is available or intended to work.

        This function automatically call and process the appropriate triggers.
        """
        tracking = mrp_productions[0].product_tracking
        sameTracking = True
        for mo in mrp_productions:
            sameTracking = sameTracking and mo.product_tracking == tracking
        self.assertTrue(sameTracking, "MOs passed to the executeConsumptionTriggers method shall have the same product_tracking")

        isSerial = tracking == 'serial'
        isAvailable = all(move.state == 'assigned' for move in mrp_productions.move_raw_ids)
        isComponentTracking = any(move.has_tracking != 'none' for move in mrp_productions.move_raw_ids)

        countOk = True
        length = len(mrp_productions)
        if isSerial:
            if isAvailable:
                countOk = length == self.SERIAL_AVAILABLE_TRIGGERS_COUNT
            else:
                countOk = length == self.SERIAL_TRIGGERS_COUNT
        else:
            if isAvailable:
                countOk = length == self.DEFAULT_AVAILABLE_TRIGGERS_COUNT
            else:
                countOk = length == self.DEFAULT_TRIGGERS_COUNT
        self.assertTrue(countOk, "The number of MOs passed to the executeConsumptionTriggers method does not match the associated TRIGGERS_COUNT")

        mrp_productions[0].qty_producing = mrp_productions[0].product_qty
        mrp_productions[0]._onchange_qty_producing()

        i = 1
        if isSerial:
            mrp_productions[i].action_generate_serial()
            i += 1

        if isAvailable:
            error = False
            try:
                mrp_productions[i].button_mark_done()
            except UserError:
                error = True

            self.assertFalse(error, "Immediate Production shall not raise an error.")