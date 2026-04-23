def _postprocess_contents(self, values):
        ICP = self.env['ir.config_parameter'].sudo().get_param
        supported_subtype = ICP('base.image_autoresize_extensions', 'png,jpeg,bmp,tiff').split(',')

        mimetype = values['mimetype'] = self._compute_mimetype(values)
        _type, _match, _subtype = mimetype.partition('/')
        is_image_resizable = _type == 'image' and _subtype in supported_subtype
        if is_image_resizable and (values.get('datas') or values.get('raw')):
            is_raw = values.get('raw')

            # Can be set to 0 to skip the resize
            max_resolution = ICP('base.image_autoresize_max_px', '1920x1920')
            if str2bool(max_resolution, True):
                try:
                    if is_raw:
                        img = image.ImageProcess(values['raw'], verify_resolution=False)
                    else:  # datas
                        img = image.ImageProcess(base64.b64decode(values['datas']), verify_resolution=False)

                    if not img.image:
                        _logger.info('Post processing ignored : Empty source, SVG, or WEBP')
                        return values

                    w, h = img.image.size
                    nw, nh = map(int, max_resolution.split('x'))
                    if w > nw or h > nh:
                        img = img.resize(nw, nh)
                        if _subtype == 'jpeg':  # Do not affect PNGs color palette
                            quality = int(ICP('base.image_autoresize_quality', 80))
                        else:
                            quality = 0
                        image_data = img.image_quality(quality=quality)
                        if is_raw:
                            values['raw'] = image_data
                        else:
                            values['datas'] = base64.b64encode(image_data)
                except UserError as e:
                    # Catch error during test where we provide fake image
                    # raise UserError(_("This file could not be decoded as an image file. Please try with a different file."))
                    msg = str(e)  # the exception can be lazy-translated, resolve it here
                    _logger.info('Post processing ignored : %s', msg)
        return values