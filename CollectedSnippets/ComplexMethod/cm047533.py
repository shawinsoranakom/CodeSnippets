def _image_process(self, value, env):
        if self.readonly and (
            (not self.max_width and not self.max_height)
            or (
                isinstance(self.related_field, Image)
                and self.max_width == self.related_field.max_width
                and self.max_height == self.related_field.max_height
            )
        ):
            # no need to process images for computed fields, or related fields
            return value
        try:
            img = base64.b64decode(value or '') or False
        except Exception as e:
            raise UserError(env._("Image is not encoded in base64.")) from e

        if img and guess_mimetype(img, '') == 'image/webp':
            if not self.max_width and not self.max_height:
                return value
            # Fetch resized version.
            Attachment = env['ir.attachment']
            checksum = Attachment._compute_checksum(img)
            origins = Attachment.search([
                ['id', '!=', False],  # No implicit condition on res_field.
                ['checksum', '=', checksum],
            ])
            if origins:
                origin_ids = [attachment.id for attachment in origins]
                resized_domain = [
                    ['id', '!=', False],  # No implicit condition on res_field.
                    ['res_model', '=', 'ir.attachment'],
                    ['res_id', 'in', origin_ids],
                    ['description', '=', 'resize: %s' % max(self.max_width, self.max_height)],
                ]
                resized = Attachment.sudo().search(resized_domain, limit=1)
                if resized:
                    # Fallback on non-resized image (value).
                    return resized.datas or value
            return value

        # delay import of image_process until this point
        from odoo.tools.image import image_process  # noqa: PLC0415
        return base64.b64encode(image_process(img,
            size=(self.max_width, self.max_height),
            verify_resolution=self.verify_resolution,
        ) or b'') or False