def shape(self, module, filename, **kwargs):
        """
        Returns a color-customized svg (background shape or illustration).
        """
        svg = None
        if module == 'illustration':
            unslug = request.env['ir.http']._unslug
            attachment = request.env['ir.attachment'].sudo().browse(unslug(filename)[1])
            if (not attachment.exists()
                    or attachment.type != 'binary'
                    or not attachment.public
                    or not attachment.url.startswith(request.httprequest.path)):
                # Fallback to URL lookup to allow using shapes that were
                # imported from data files.
                attachment = request.env['ir.attachment'].sudo().search([
                    ('type', '=', 'binary'),
                    ('public', '=', True),
                    ('url', '=', request.httprequest.path),
                ], limit=1)
                if not attachment:
                    raise werkzeug.exceptions.NotFound()

            if not re.match(r'^image\/svg\+xml(;.*)?$', attachment.mimetype):
                return request.make_response(attachment.raw, [
                    ('Content-type', attachment.mimetype),
                    ('Cache-control', 'max-age=%s' % http.STATIC_CACHE_LONG),
                ])

            svg = attachment.raw.decode('utf-8')
        else:
            # Used for compatibility
            if module == 'web_editor':
                module = 'html_builder'
            svg = self._get_shape_svg(module, 'shapes', filename)

        svg, options = self._update_svg_colors(kwargs, svg)
        flip_value = options.get('flip', False)
        if flip_value == 'x':
            svg = svg.replace('<svg ', '<svg style="transform: scaleX(-1);" ', 1)
        elif flip_value == 'y':
            svg = svg.replace('<svg ', '<svg style="transform: scaleY(-1)" ', 1)
        elif flip_value == 'xy':
            svg = svg.replace('<svg ', '<svg style="transform: scale(-1)" ', 1)

        shape_animation_speed = float(options.get('shapeAnimationSpeed', 0.0))
        if shape_animation_speed != 0.0:
            svg = self.replace_animation_duration(
                shape_animation_speed=shape_animation_speed,
                svg=svg
            )
        return request.make_response(svg, [
            ('Content-type', 'image/svg+xml'),
            ('Cache-control', 'max-age=%s' % http.STATIC_CACHE_LONG),
        ])