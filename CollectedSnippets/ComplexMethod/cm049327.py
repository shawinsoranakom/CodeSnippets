def clear_product_images(self, product_product_id, product_template_id):
        """
        Unlinks all images from the product.
        """
        if not request.env.user.has_group('website.group_website_restricted_editor'):
            raise NotFound()

        product_product = request.env['product.product'].browse(int(product_product_id)) if product_product_id else False
        product_template = request.env['product.template'].browse(int(product_template_id)) if product_template_id else False

        if product_product and not product_template:
            product_template = product_product.product_tmpl_id

        if product_product and product_product.product_variant_image_ids:
            product_product.product_variant_image_ids.unlink()
        else:
            product_template.product_template_image_ids.unlink()