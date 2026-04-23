def _update_svg_colors(self, options, svg):
        user_colors = []
        svg_options = {}
        default_palette = {
            '1': '#3AADAA',
            '2': '#7C6576',
            '3': '#F6F6F6',
            '4': '#FFFFFF',
            '5': '#383E45',
        }
        bundle_css = None
        regex_hex = r'#[0-9A-F]{6,8}'
        regex_rgba = r'rgba?\(\d{1,3}, ?\d{1,3}, ?\d{1,3}(?:, ?[0-9.]{1,4})?\)'
        for key, value in options.items():
            colorMatch = re.match('^c([1-5])$', key)
            if colorMatch:
                css_color_value = value
                # Check that color is hex or rgb(a) to prevent arbitrary injection
                if not re.match(r'(?i)^%s$|^%s$' % (regex_hex, regex_rgba), css_color_value.replace(' ', '')):
                    if re.match('^o-color-([1-5])$', css_color_value):
                        if not bundle_css:
                            bundle = 'web.assets_frontend'
                            asset = request.env["ir.qweb"]._get_asset_bundle(bundle)
                            bundle_css = asset.css().index_content
                        color_search = re.search(r'(?i)--%s:\s+(%s|%s)' % (css_color_value, regex_hex, regex_rgba), bundle_css)
                        if not color_search:
                            raise werkzeug.exceptions.BadRequest()
                        css_color_value = color_search.group(1)
                    else:
                        raise werkzeug.exceptions.BadRequest()
                user_colors.append([tools.html_escape(css_color_value), colorMatch.group(1)])
            else:
                svg_options[key] = value

        color_mapping = {default_palette[palette_number]: color for color, palette_number in user_colors}
        # create a case-insensitive regex to match all the colors to replace, eg: '(?i)(#3AADAA)|(#7C6576)'
        regex = '(?i)%s' % '|'.join('(%s)' % color for color in color_mapping.keys())

        def subber(match):
            key = match.group().upper()
            return color_mapping[key] if key in color_mapping else key
        return re.sub(regex, subber, svg), svg_options