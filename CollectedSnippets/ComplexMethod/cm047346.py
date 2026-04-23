def barcode(self, barcode_type, value, **kwargs):
        defaults = {
            'width': (600, int),
            'height': (100, int),
            'humanreadable': (False, lambda x: bool(int(x))),
            'quiet': (True, lambda x: bool(int(x))),
            'mask': (None, lambda x: x),
            'barBorder': (4, int),
            # The QR code can have different layouts depending on the Error Correction Level
            # See: https://en.wikipedia.org/wiki/QR_code#Error_correction
            # Level 'L' – up to 7% damage   (default)
            # Level 'M' – up to 15% damage  (i.e. required by l10n_ch QR bill)
            # Level 'Q' – up to 25% damage
            # Level 'H' – up to 30% damage
            'barLevel': ('L', lambda x: x in ('L', 'M', 'Q', 'H') and x or 'L'),
        }
        kwargs = {k: validator(kwargs.get(k, v)) for k, (v, validator) in defaults.items()}
        kwargs['humanReadable'] = kwargs.pop('humanreadable')
        if kwargs['humanReadable']:
            kwargs['fontName'] = get_barcode_font()

        if kwargs['width'] * kwargs['height'] > 1200000 or max(kwargs['width'], kwargs['height']) > 10000:
            raise ValueError("Barcode too large")

        if barcode_type == 'UPCA' and len(value) in (11, 12, 13):
            barcode_type = 'EAN13'
            if len(value) in (11, 12):
                value = '0%s' % value
        elif barcode_type == 'auto':
            symbology_guess = {8: 'EAN8', 13: 'EAN13'}
            barcode_type = symbology_guess.get(len(value), 'Code128')
        elif barcode_type == 'QR':
            # for `QR` type, `quiet` is not supported. And is simply ignored.
            # But we can use `barBorder` to get a similar behaviour.
            # quiet=True & barBorder=4 by default cf above, remove border only if quiet=False
            if not kwargs['quiet']:
                kwargs['barBorder'] = 0

        if barcode_type in ('EAN8', 'EAN13') and not check_barcode_encoding(value, barcode_type):
            # If the barcode does not respect the encoding specifications, convert its type into Code128.
            # Otherwise, the report-lab method may return a barcode different from its value. For instance,
            # if the barcode type is EAN-8 and the value 11111111, the report-lab method will take the first
            # seven digits and will compute the check digit, which gives: 11111115 -> the barcode does not
            # match the expected value.
            barcode_type = 'Code128'

        try:
            barcode = createBarcodeDrawing(barcode_type, value=value, format='png', **kwargs)

            # If a mask is asked and it is available, call its function to
            # post-process the generated QR-code image
            if kwargs['mask']:
                available_masks = self.get_available_barcode_masks()
                mask_to_apply = available_masks.get(kwargs['mask'])
                if mask_to_apply:
                    mask_to_apply(kwargs['width'], kwargs['height'], barcode)

            return barcode.asString('png')
        except (ValueError, AttributeError):
            if barcode_type == 'Code128':
                raise ValueError("Cannot convert into barcode.")
            elif barcode_type == 'QR':
                raise ValueError("Cannot convert into QR code.")
            else:
                return self.barcode('Code128', value, **kwargs)