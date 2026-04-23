def write(self, vals):
        """Override to make sure attribute type can't be changed if it's used on
        a product template.

        This is important to prevent because changing the type would make
        existing combinations invalid without recomputing them, and recomputing
        them might take too long and we don't want to change products without
        the user knowing about it."""
        if 'create_variant' in vals:
            for pa in self:
                if vals['create_variant'] != pa.create_variant and pa.number_related_products:
                    raise UserError(_(
                        "You cannot change the Variants Creation Mode of the attribute %(attribute)s"
                        " because it is used on the following products:\n%(products)s",
                        attribute=pa.display_name,
                        products=", ".join(pa.product_tmpl_ids.mapped('display_name')),
                    ))
        invalidate = 'sequence' in vals and any(record.sequence != vals['sequence'] for record in self)
        res = super().write(vals)
        if invalidate:
            # prefetched o2m have to be resequenced
            # (eg. product.template: attribute_line_ids)
            self.env.flush_all()
            self.env.invalidate_all()
        return res