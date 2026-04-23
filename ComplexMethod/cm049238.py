def _is_applicable_for(self, product, qty_in_product_uom):
        """Check whether the current rule is valid for the given product & qty.

        Note: self.ensure_one()

        :param product: product record (product.product/product.template)
        :param float qty_in_product_uom: quantity, expressed in product UoM
        :returns: Whether rules is valid or not
        :rtype: bool
        """
        self.ensure_one()
        product.ensure_one()
        res = True

        is_product_template = product._name == 'product.template'
        if self.min_quantity and qty_in_product_uom < self.min_quantity:
            res = False

        elif self.applied_on == "2_product_category":
            if not product.categ_id or (
                product.categ_id != self.categ_id
                and not product.categ_id.parent_path.startswith(self.categ_id.parent_path)
            ):
                res = False
        # Applied on a specific product template/variant
        elif is_product_template:
            if self.applied_on == "1_product" and product.id != self.product_tmpl_id.id:
                res = False
            elif self.applied_on == "0_product_variant" and not (
                product.product_variant_count == 1
                and product.product_variant_id.id == self.product_id.id
            ):
                # product self acceptable on template if has only one variant
                res = False
        elif (
            self.applied_on == "1_product"
            and product.product_tmpl_id.id != self.product_tmpl_id.id
        ) or (
            self.applied_on == "0_product_variant" and product.id != self.product_id.id
        ):
            res = False

        return res