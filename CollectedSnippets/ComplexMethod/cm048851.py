def action_purchase_order_suggest(self):
        """ Adds suggested products to PO, removing products with no suggested_qty, and
        collapsing existing po_lines into at most 1 orderline. Saves suggestion params
        (eg. number_of_days) to partner table. """
        self.ensure_one()
        ctx = self.env.context
        domain = [('type', '=', 'consu')]
        if ctx.get("suggest_domain"):
            domain = fields.Domain.AND([domain, ctx.get("suggest_domain")])
        products = self.env['product.product'].search(domain)

        self.partner_id.sudo().write({
            'suggest_days': ctx.get('suggest_days'),
            'suggest_based_on': ctx.get('suggest_based_on'),
            'suggest_percent': ctx.get('suggest_percent'),
        })

        po_lines_commands = []
        for product in products:
            suggest_line = self.env['purchase.order.line']._prepare_purchase_order_line(
                product,
                product.suggested_qty,
                product.uom_id,
                self.company_id,
                self.partner_id,
                self
            )
            existing_lines = self.order_line.filtered(lambda pol: pol.product_id == product)
            if section_id := ctx.get("section_id"):
                existing_lines = existing_lines.filtered(lambda pol: pol.get_parent_section_line().id == section_id)
                suggest_line["sequence"] = self._get_new_line_sequence("order_line", section_id)
            else:
                existing_lines = existing_lines.filtered(lambda pol: not pol.parent_id)  # lines with no sections
            if existing_lines:
                # Collapse into 1 or 0 po line, discarding previous data in favor of suggested qtys
                to_unlink = existing_lines if product.suggested_qty == 0 else existing_lines[:-1]
                po_lines_commands += [Command.unlink(line.id) for line in to_unlink]
                if product.suggested_qty > 0:
                    po_lines_commands.append(Command.update(existing_lines[-1].id, suggest_line))
            elif product.suggested_qty > 0:
                po_lines_commands.append(Command.create(suggest_line))

        self.order_line = po_lines_commands
        # Return the change in number of po_lines for the given section
        return sum({"CREATE": 1, "UNLINK": -1}.get(line[0].name, 0) for line in po_lines_commands)