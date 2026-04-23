def _bom_find(self, products, picking_type=None, company_id=False, bom_type=False):
        """ Find the first BoM for each products

        :param products: `product.product` recordset
        :return: One bom (or empty recordset `mrp.bom` if none find) by product (`product.product` record)
        :rtype: defaultdict(`lambda: self.env['mrp.bom']`)
        """
        bom_by_product = defaultdict(lambda: self.env['mrp.bom'])
        products = products.filtered(lambda p: p.type != 'service')
        if not products:
            return bom_by_product
        domain = self._bom_find_domain(products, picking_type=picking_type, company_id=company_id, bom_type=bom_type)

        # Performance optimization, allow usage of limit and avoid the for loop `bom.product_tmpl_id.product_variant_ids`
        if len(products) == 1:
            bom = self.search(domain, order='sequence, product_id, id', limit=1)
            if bom:
                bom_by_product[products] = bom
            return bom_by_product

        boms = self.search(domain, order='sequence, product_id, id')

        products_ids = set(products.ids)
        for bom in boms:
            products_implies = bom.product_id or bom.product_tmpl_id.product_variant_ids
            for product in products_implies:
                if product.id in products_ids and product not in bom_by_product:
                    bom_by_product[product] = bom

        return bom_by_product