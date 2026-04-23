def export_icon_to_png(self, icon, color='#000', bg=None, size=100, alpha=255, font='/web/static/src/libs/fontawesome/fonts/fontawesome-webfont.ttf', width=None, height=None):
        """ This method converts an unicode character to an image (using Font
            Awesome font by default) and is used only for mass mailing because
            custom fonts are not supported in mail.
            :param icon : decimal encoding of unicode character
            :param color : RGB code of the color
            :param bg : RGB code of the background color
            :param size : Pixels in integer
            :param alpha : transparency of the image from 0 to 255
            :param font : font path
            :param width : Pixels in integer
            :param height : Pixels in integer

            :returns PNG image converted from given font
        """
        # For custom icons, use the corresponding custom font
        if icon.isdigit():
            oi_font_char_codes = {
                # Replacement of existing Twitter icons by X icons (the route
                # here receives the old icon code always, but the replacement
                # one is also considered for consistency anyway).
                "61569": "59464",  # F081 -> E848: fa-twitter-square
                "61593": "59418",  # F099 -> E81A: fa-twitter

                # Addition of new icons
                "59407": "59407",  # E80F: fa-strava
                "59409": "59409",  # E811: fa-discord
                "59416": "59416",  # E818: fa-threads
                "59417": "59417",  # E819: fa-kickstarter
                "59419": "59419",  # E81B: fa-tiktok
                "59420": "59420",  # E81C: fa-bluesky
                "59421": "59421",  # E81D: fa-google-play
            }
            if icon in oi_font_char_codes:
                icon = oi_font_char_codes[icon]
                font = "/web/static/lib/odoo_ui_icons/fonts/odoo_ui_icons.woff"

        size = max(width, height, 1) if width else size
        width = width or size
        height = height or size
        # Make sure we have at least size=1
        width = max(1, min(width, 512))
        height = max(1, min(height, 512))
        # Initialize font
        if font.startswith('/'):
            font = font[1:]
        font_obj = ImageFont.truetype(file_open(font, 'rb'), height)

        # if received character is not a number, keep old behaviour (icon is character)
        icon = chr(int(icon)) if icon.isdigit() else icon

        # Background standardization
        if bg is not None and bg.startswith('rgba'):
            bg = bg.replace('rgba', 'rgb')
            bg = ','.join(bg.split(',')[:-1]) + ')'

        # Convert the opacity value compatible with PIL Image color (0 to 255)
        # when color specifier is 'rgba'
        if color is not None and color.startswith('rgba'):
            *rgb, a = color.strip(')').split(',')
            opacity = str(floor(float(a) * 255))
            color = ','.join([*rgb, opacity]) + ')'

        # Determine the dimensions of the icon
        image = Image.new("RGBA", (width, height), color)
        draw = ImageDraw.Draw(image)

        if hasattr(draw, 'textbbox'):
            box = draw.textbbox((0, 0), icon, font=font_obj)
            left = box[0]
            top = box[1]
            boxw = box[2] - box[0]
            boxh = box[3] - box[1]
        else:  # pillow < 8.00 (Focal)
            left, top, _right, _bottom = image.getbbox()
            boxw, boxh = draw.textsize(icon, font=font_obj)

        draw.text((0, 0), icon, font=font_obj)

        # Create an alpha mask
        imagemask = Image.new("L", (boxw, boxh), 0)
        drawmask = ImageDraw.Draw(imagemask)
        drawmask.text((-left, -top), icon, font=font_obj, fill=255)

        # Create a solid color image and apply the mask
        if color.startswith('rgba'):
            color = color.replace('rgba', 'rgb')
            color = ','.join(color.split(',')[:-1]) + ')'
        iconimage = Image.new("RGBA", (boxw, boxh), color)
        iconimage.putalpha(imagemask)

        # Create output image
        outimage = Image.new("RGBA", (boxw, height), bg or (0, 0, 0, 0))
        outimage.paste(iconimage, (left, top), iconimage)

        # output image
        output = io.BytesIO()
        outimage.save(output, format="PNG")
        output.seek(0)
        response = send_file(
            output,
            request.httprequest.environ,
            mimetype='image/png',
            conditional=False,
            etag=False,
            max_age=STATIC_CACHE,
            response_class=Response,
        )
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST'
        return response