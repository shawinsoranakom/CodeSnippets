def resequence_product_image(self, image_res_model, image_res_id, move):
        """
        Move the product image in the given direction and update all images' sequence.

        :param str image_res_model: The model of the image. It can be 'product.template',
                                    'product.product', or 'product.image'.
        :param str image_res_id: The record ID of the image to move.
        :param str move: The direction of the move. It can be 'first', 'left', 'right', or 'last'.
        :raises NotFound: If the user does not have the required permissions, if the model of the
                          image is not allowed, or if the move direction is not allowed.
        :raise ValidationError: If the product is not found.
        :raise ValidationError: If the image to move is not found in the product images.
        :raise ValidationError: If a video is moved to the first position.
        :return: None
        """
        if (
            not request.env.user.has_group('website.group_website_restricted_editor')
            or image_res_model not in ['product.product', 'product.template', 'product.image']
            or move not in ['first', 'left', 'right', 'last']
        ):
            raise NotFound()

        image_res_id = int(image_res_id)
        image_to_resequence = request.env[image_res_model].browse(image_res_id)
        if image_res_model == 'product.product':
            product = image_to_resequence
            product_template = product.product_tmpl_id
        elif image_res_model == 'product.template':
            product_template = image_to_resequence
            product = product_template.product_variant_id
        else:
            product = image_to_resequence.product_variant_id
            product_template = product.product_tmpl_id or image_to_resequence.product_tmpl_id

        if not product and not product_template:
            raise ValidationError(_("Product not found"))

        product_images = (product or product_template)._get_images()
        if image_to_resequence not in product_images:
            raise ValidationError(_("Invalid image"))

        image_idx = product_images.index(image_to_resequence)
        new_image_idx = 0
        if move == 'left':
            new_image_idx = max(0, image_idx - 1)
        elif move == 'right':
            new_image_idx = min(len(product_images) - 1, image_idx + 1)
        elif move == 'last':
            new_image_idx = len(product_images) - 1

        # no-op resequences
        if new_image_idx == image_idx:
            return

        # Reorder images locally.
        product_images.insert(new_image_idx, product_images.pop(image_idx))

        # If the main image has been reordered (i.e. it's no longer in first position), use the
        # image that's now in first position as main image instead.
        # Additional images are product.image records. The main image is a product.product or
        # product.template record.
        main_image_idx = next(
            idx for idx, image in enumerate(product_images) if image._name != 'product.image'
        )
        if main_image_idx != 0:
            main_image = product_images[main_image_idx]
            additional_image = product_images[0]
            if additional_image.video_url:
                raise ValidationError(_("You can't use a video as the product's main image."))
            # Swap records.
            product_images[main_image_idx], product_images[0] = additional_image, main_image
            # Swap image data.
            main_image.image_1920, additional_image.image_1920 = (
                additional_image.image_1920, main_image.image_1920
            )
            additional_image.name = main_image.name  # Update image name but not product name.

        # Resequence additional images according to the new ordering.
        for idx, product_image in enumerate(product_images):
            if product_image._name == 'product.image':
                product_image.sequence = idx