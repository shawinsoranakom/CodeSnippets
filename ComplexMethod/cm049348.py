def _is_applicable_for(self, product, price_data):
        """Return whether the product matches the criteria of the ribbon automatic assignment.

        :param product.product product: the displayed product
        :param dict price_data: price information for the given product
            (sales price for shop page, combination information for product page)

        :return: Whether the ribbon matches the given product and price.
        :rtype: bool
        """
        self.ensure_one()

        # Check if a discount is applied to the product using a pricelist, comparison price, or
        # others.
        if (  # noqa: SIM103
            self.assign == 'sale'
            and price_data
            and (
                # for /shop page
                (
                    'base_price' in price_data
                    and (price_data['base_price'] > price_data['price_reduce'])
                )
                # for /product page
                or (
                    'compare_list_price' in price_data
                    and price_data['compare_list_price'] > price_data['price']
                )
                or price_data.get('has_discounted_price')
            )
        ):
            return True
        # Check if the product is published within the ribbon's new period.
        if (  # noqa: SIM103
            self.assign == 'new'
            and self.new_period >= (fields.Datetime.today() - product.publish_date).days
        ):
            return True
        return False