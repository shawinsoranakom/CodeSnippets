def _output_type_handler(cursor, name, defaultType, length, precision, scale):
        """
        Called for each db column fetched from cursors. Return numbers as the
        appropriate Python type, and NCLOB with JSON as strings.
        """
        if defaultType == Database.NUMBER:
            if scale == -127:
                if precision == 0:
                    # NUMBER column: decimal-precision floating point.
                    # This will normally be an integer from a sequence,
                    # but it could be a decimal value.
                    outconverter = FormatStylePlaceholderCursor._output_number_converter
                else:
                    # FLOAT column: binary-precision floating point.
                    # This comes from FloatField columns.
                    outconverter = float
            elif precision > 0:
                # NUMBER(p,s) column: decimal-precision fixed point.
                # This comes from IntegerField and DecimalField columns.
                outconverter = FormatStylePlaceholderCursor._get_decimal_converter(
                    precision, scale
                )
            else:
                # No type information. This normally comes from a
                # mathematical expression in the SELECT list. Guess int
                # or Decimal based on whether it has a decimal point.
                outconverter = FormatStylePlaceholderCursor._output_number_converter
            return cursor.var(
                Database.STRING,
                size=255,
                arraysize=cursor.arraysize,
                outconverter=outconverter,
            )
        # oracledb 2.0.0+ returns NLOB columns with IS JSON constraints as
        # dicts. Use a no-op converter to avoid this.
        elif defaultType == Database.DB_TYPE_NCLOB:
            return cursor.var(Database.DB_TYPE_NCLOB, arraysize=cursor.arraysize)