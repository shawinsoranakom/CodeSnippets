def value_to_html(self, value, options=None):
        if not value:
            return ''
        if not bool(re.match(r'^[\x00-\x7F]+$', value)):
            return nl2br(value)
        barcode_symbology = options.get('symbology', 'Code128')
        barcode = self.env['ir.actions.report'].barcode(
            barcode_symbology,
            value,
            **{key: value for key, value in options.items() if key in ['width', 'height', 'humanreadable', 'quiet', 'mask']})

        img_element = html.Element('img')
        for k, v in options.items():
            if k.startswith('img_') and k[4:] in safe_attrs:
                img_element.set(k[4:], v)
        if not img_element.get('alt'):
            img_element.set('alt', _('Barcode %s', value))
        img_element.set('src', 'data:image/png;base64,%s' % base64.b64encode(barcode).decode())
        return Markup(html.tostring(img_element, encoding='unicode'))