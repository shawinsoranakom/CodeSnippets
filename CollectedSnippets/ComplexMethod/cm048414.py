def get_aggregate_barcodes(self):
        """ Generates and aggregates quants' barcodes. This method uses the config parameters
        `stock.agg_barcode_max_length` to determine the length limit of a single aggregate barcode
        (400 by default) and `stock.barcode_separator` to determine which character to use to
        separate individual encodings (this method can't work without this parameter and will return
        an empty list.) Depending on the number of quants, those parameters and the length of their
        barcode encodings, there can be one or more aggregate barcodes.

        :return: list
        """
        agg_barcode_max_length = int(self.env['ir.config_parameter'].sudo().get_param('stock.agg_barcode_max_length', 400))
        barcode_separator = self.env['ir.config_parameter'].sudo().get_param('stock.barcode_separator')
        if not barcode_separator:
            return []  # A barcode separator is mandatory to be able to aggregate barcodes.

        eol_char = '\t'  # Added at the end of aggregate barcodes to end `barcode_scanned` event.
        aggregate_barcodes = []
        aggregate_barcode = ""

        # Searches all GS1 rules linked to an UoM other than Unit and retrieves their AI.
        uom_unit_id = self.env.ref('uom.product_uom_unit').id
        gs1_quantity_rules = self.env['barcode.rule'].search([
            ('associated_uom_id', '!=', False),
            ('associated_uom_id', '!=', uom_unit_id),
            ('is_gs1_nomenclature', '=', True)]
        )
        gs1_quantity_rules_ai_by_uom = {}

        for rule in gs1_quantity_rules:
            decimal = str(len(f'{rule.associated_uom_id.rounding:.10f}'.rstrip('0').split('.')[1]))
            rule_ai = rule.pattern[1:4] + decimal
            gs1_quantity_rules_ai_by_uom[rule.associated_uom_id.id] = rule_ai

        previous_product = self.env['product.product']
        for quant in self:
            if not quant.product_id.barcode:
                continue
            barcode = ""
            # In case the quant product's barcode is not GS1 compliant, add it first,
            # so that the lots and qty barcodes that follow it will be used for this product.
            if previous_product != quant.product_id:
                previous_product = quant.product_id
                if not quant.product_id.valid_ean:
                    barcode += quant.product_id.barcode
            # Gets quant's barcode (either a GS1 barcode or only a serial number.)
            quant_gs1_barcode = quant._get_gs1_barcode(gs1_quantity_rules_ai_by_uom)
            if quant_gs1_barcode:
                barcode += (barcode_separator if barcode else '') + quant_gs1_barcode
            elif quant.tracking == 'serial':
                barcode += (barcode_separator if barcode else '') + quant.lot_id.name
            # If aggregate barcode will be too long, adds it to the result list and resets it.
            if aggregate_barcode and len(aggregate_barcode + barcode) > agg_barcode_max_length:
                aggregate_barcodes.append(aggregate_barcode + eol_char)
                aggregate_barcode = ""
            if barcode:
                if aggregate_barcode and aggregate_barcode[-1] != barcode_separator:
                    aggregate_barcode += barcode_separator
                aggregate_barcode += barcode

        if aggregate_barcode:
            aggregate_barcodes.append(aggregate_barcode + eol_char)

        return aggregate_barcodes