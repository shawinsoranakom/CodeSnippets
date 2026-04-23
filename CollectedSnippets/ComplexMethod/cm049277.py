def extract_image_primary_secondary_colors(self, logo, white_threshold=225, mitigate=175):
        """
        Identifies dominant colors

        First resizes the original image to improve performance, then discards
        transparent colors and white-ish colors, then calls the averaging
        method twice to evaluate both primary and secondary colors.

        :param logo: logo to process
        :param white_threshold: arbitrary value defining the maximum value a color can reach
        :param mitigate: arbitrary value defining the maximum value a band can reach

        :return: a 2-value tuple with hex values of primary and secondary colors
        """
        if not logo:
            return False, False
        # The "===" gives different base64 encoding a correct padding
        logo += b'===' if isinstance(logo, bytes) else '==='
        try:
            # Catches exceptions caused by logo not being an image
            image = tools.image_fix_orientation(tools.base64_to_image(logo))
        except Exception:
            return False, False

        base_w, base_h = image.size
        w = ceil(50 * base_w / base_h)
        h = 50

        # Converts to RGBA (if already RGBA, this is a noop)
        image_converted = image.convert('RGBA')
        image_resized = image_converted.resize((w, h), resample=Resampling.NEAREST)

        colors = []
        for color in image_resized.getcolors(w * h):
            if not(color[1][0] > white_threshold and
                   color[1][1] > white_threshold and
                   color[1][2] > white_threshold) and color[1][3] > 0:
                colors.append(color)

        if not colors:  # May happen when the whole image is white
            return False, False
        primary, remaining = tools.average_dominant_color(colors, mitigate=mitigate)
        secondary = tools.average_dominant_color(remaining, mitigate=mitigate)[0] if remaining else primary

        # Lightness and saturation are calculated here.
        # - If both colors have a similar lightness, the most colorful becomes primary
        # - When the difference in lightness is too great, the brightest color becomes primary
        l_primary = tools.get_lightness(primary)
        l_secondary = tools.get_lightness(secondary)
        if (l_primary < 0.2 and l_secondary < 0.2) or (l_primary >= 0.2 and l_secondary >= 0.2):
            s_primary = tools.get_saturation(primary)
            s_secondary = tools.get_saturation(secondary)
            if s_primary < s_secondary:
                primary, secondary = secondary, primary
        elif l_secondary > l_primary:
            primary, secondary = secondary, primary

        return tools.rgb_to_hex(primary), tools.rgb_to_hex(secondary)