def write(self, vals):
        values = vals
        if 'display_type' in values:
            new_type = values.get('display_type')
            invalid_lines = self.filtered(
                lambda line:
                    line.display_type != new_type
                    and not (line.display_type == 'line_subsection' and new_type == 'line_section')
            )
            if invalid_lines:
                raise UserError(_(
                    "You cannot change the type of a sale order line. Instead you should "
                    "delete the current line and create a new line of the proper type."
                ))

        if 'product_id' in values and any(
            sol.product_id.id != values['product_id']
            and not sol.product_updatable
            for sol in self
        ):
            raise UserError(_("You cannot modify the product of this order line."))

        if 'product_uom_qty' in values:
            precision = self.env['decimal.precision'].precision_get('Product Unit')
            self.filtered(
                lambda r: r.state == 'sale' and float_compare(r.product_uom_qty, values['product_uom_qty'], precision_digits=precision) != 0)._update_line_quantity(values)

        if (
            'technical_price_unit' in values
            and 'price_unit' not in values
            and not self.env.context.get('sale_write_from_compute')
        ):
            # price_unit field was set as readonly in the view (but technical_price_unit not)
            # the field is not sent by the client and expected to be recomputed, but isn't
            # because technical_price_unit is set.
            values.pop('technical_price_unit')

        # Prevent writing on a locked SO.
        protected_fields = self._get_protected_fields()
        if any(self.order_id.mapped('locked')) and any(f in values.keys() for f in protected_fields):
            protected_fields_modified = list(set(protected_fields) & set(values.keys()))

            if 'name' in protected_fields_modified and all(self.mapped('is_downpayment')):
                protected_fields_modified.remove('name')

            fields = self.env['ir.model.fields'].sudo().search([
                ('name', 'in', protected_fields_modified), ('model', '=', self._name)
            ])
            if fields:
                raise UserError(
                    _('It is forbidden to modify the following fields in a locked order:\n%s',
                      '\n'.join(fields.mapped('field_description')))
                )

        return super().write(values)