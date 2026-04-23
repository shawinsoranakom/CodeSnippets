def format_escpos(self, im):
        # Epson support different command to print pictures.
        # We use by default "GS v 0", but it  is incompatible with certain
        # printer models (like TM-U2x0)
        # As we are pretty limited in the information that we have, we will
        # use the printer name to parse some configuration value
        # Printer name examples:
        # EpsonTMM30
        #  -> Print using raster mode
        # TM-U220__IMC_LDV_LDH_SCALE70__
        #  -> Print using column bit image mode (without vertical and
        #  horizontal density and a scale of 70%)

        # Default image printing mode
        image_mode = 'raster'

        options_str = self.device_name.split('__')
        option_str = ""
        if len(options_str) > 2:
            option_str = options_str[1].upper()
            if option_str.startswith('IMC'):
                image_mode = 'column'

        if image_mode == 'raster':
            return self.format_escpos_bit_image_raster(im)

        # Default printing mode parameters
        high_density_vertical = True
        high_density_horizontal = True
        scale = 100

        # Parse the printer name to get the needed parameters
        # The separator need to not be filtered by `get_identifier`
        options = option_str.split('_')
        for option in options:
            if option == 'LDV':
                high_density_vertical = False
            elif option == 'LDH':
                high_density_horizontal = False
            elif option.startswith('SCALE'):
                scale_value_str = re.search(r'\d+$', option)
                if scale_value_str is not None:
                    scale = int(scale_value_str.group())
                else:
                    raise ValueError("Missing printer SCALE parameter integer value in option: " + option)

        return self.format_escpos_bit_image_column(im, high_density_vertical, high_density_horizontal, scale)