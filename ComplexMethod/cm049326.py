def add_product_media(self, media, type, product_product_id, product_template_id, combination_ids=None):
        """
        Handles adding both images and videos to product variants or templates,
        links all of them to product.
        :param type: [...] can be either image or video
        :raises NotFound : If the user is not allowed to access Attachment model
        """

        if not request.env.user.has_group('website.group_website_restricted_editor'):
            raise NotFound()

        if type == 'image':  # Image case
            image_ids = request.env["ir.attachment"].browse(i['id'] for i in media)
            media_create_data = [Command.create({
                'name': image.name,   # Images uploaded from url do not have any datas. This recovers them manually
                'image_1920': image.datas
                    if image.datas
                    else request.env['ir.qweb.field.image'].load_remote_url(image.url),
            }) for image in image_ids]
        elif type == 'video':  # Video case
            video_data = media[0]
            thumbnail = None
            if video_data.get('src'):  # Check if a valid video URL is provided
                try:
                    thumbnail = base64.b64encode(get_video_thumbnail(video_data['src']))
                except Exception:
                    thumbnail = None
            else:
                raise ValidationError(_("Invalid video URL provided."))
            media_create_data = [Command.create({
                'name': video_data.get('name', 'Odoo Video'),
                'video_url': video_data['src'],
                'image_1920': thumbnail,
            })]

        product_product = request.env['product.product'].browse(int(product_product_id)) if product_product_id else False
        product_template = request.env['product.template'].browse(int(product_template_id)) if product_template_id else False

        if product_product and not product_template:
            product_template = product_product.product_tmpl_id

        if not product_product and product_template and product_template.has_dynamic_attributes():
            combination = request.env['product.template.attribute.value'].browse(combination_ids)
            product_product = product_template._get_variant_for_combination(combination)
            if not product_product:
                product_product = product_template._create_product_variant(combination)
        if product_template.has_configurable_attributes and product_product and not all(pa.create_variant == 'no_variant' for pa in product_template.attribute_line_ids.attribute_id):
            product_product.write({
                'product_variant_image_ids': media_create_data
            })
        else:
            product_template.write({
                'product_template_image_ids': media_create_data
            })