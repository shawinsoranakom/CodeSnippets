def write(self, vals):
        if 'attribute_id' in vals:
            for pav in self:
                if pav.attribute_id.id != vals['attribute_id'] and pav.is_used_on_products:
                    raise UserError(_(
                        "You cannot change the attribute of the value %(value)s because it is used"
                        " on the following products: %(products)s",
                        value=pav.display_name,
                        products=", ".join(pav.pav_attribute_line_ids.product_tmpl_id.mapped('display_name')),
                    ))

        invalidate = 'sequence' in vals and any(record.sequence != vals['sequence'] for record in self)
        res = super().write(vals)
        if invalidate:
            # prefetched o2m have to be resequenced
            # (eg. product.template.attribute.line: value_ids)
            self.env.flush_all()
            self.env.invalidate_all()
        return res