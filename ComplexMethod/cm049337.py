def change_product_config(self, product_id, **options):
        if not request.env.user.has_group('website.group_website_restricted_editor'):
            raise NotFound()

        product = request.env['product.template'].browse(product_id)
        if "sequence" in options:
            sequence = options["sequence"]
            if sequence == "top":
                product.set_sequence_top()
            elif sequence == "bottom":
                product.set_sequence_bottom()
            elif sequence == "up":
                product.set_sequence_up()
            elif sequence == "down":
                product.set_sequence_down()
        if {"x", "y"} <= set(options):
            product.write({'website_size_x': options["x"], 'website_size_y': options["y"]})