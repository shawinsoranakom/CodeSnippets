def verify_ogr_field(self, ogr_field, model_field):
        """
        Verify if the OGR Field contents are acceptable to the model field. If
        they are, return the verified value, otherwise raise an exception.
        """
        if isinstance(ogr_field, OFTString) and isinstance(
            model_field, (models.CharField, models.TextField)
        ):
            if self.encoding and ogr_field.value is not None:
                # The encoding for OGR data sources may be specified here
                # (e.g., 'cp437' for Census Bureau boundary files).
                val = force_str(ogr_field.value, self.encoding)
            else:
                val = ogr_field.value
            if (
                model_field.max_length
                and val is not None
                and len(val) > model_field.max_length
            ):
                raise InvalidString(
                    "%s model field maximum string length is %s, given %s characters."
                    % (model_field.name, model_field.max_length, len(val))
                )
        elif isinstance(ogr_field, OFTReal) and isinstance(
            model_field, models.DecimalField
        ):
            try:
                # Creating an instance of the Decimal value to use.
                d = Decimal(str(ogr_field.value))
            except DecimalInvalidOperation:
                raise InvalidDecimal(
                    "Could not construct decimal from: %s" % ogr_field.value
                )

            # Getting the decimal value as a tuple.
            dtup = d.as_tuple()
            digits = dtup[1]
            d_idx = dtup[2]  # index where the decimal is

            # Maximum amount of precision, or digits to the left of the
            # decimal.
            max_prec = model_field.max_digits - model_field.decimal_places

            # Getting the digits to the left of the decimal place for the
            # given decimal.
            if d_idx < 0:
                n_prec = len(digits[:d_idx])
            else:
                n_prec = len(digits) + d_idx

            # If we have more than the maximum digits allowed, then throw an
            # InvalidDecimal exception.
            if n_prec > max_prec:
                raise InvalidDecimal(
                    "A DecimalField with max_digits %d, decimal_places %d must "
                    "round to an absolute value less than 10^%d."
                    % (model_field.max_digits, model_field.decimal_places, max_prec)
                )
            val = d
        elif isinstance(ogr_field, (OFTReal, OFTString)) and isinstance(
            model_field, models.IntegerField
        ):
            # Attempt to convert any OFTReal and OFTString value to an
            # OFTInteger.
            try:
                val = int(ogr_field.value)
            except ValueError:
                raise InvalidInteger(
                    "Could not construct integer from: %s" % ogr_field.value
                )
        else:
            val = ogr_field.value
        return val