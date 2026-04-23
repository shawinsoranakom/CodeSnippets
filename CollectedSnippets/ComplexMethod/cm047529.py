def convert_to_column(self, value, record, values=None, validate=True):
        # Binary values may be byte strings (python 2.6 byte array), but
        # the legacy OpenERP convention is to transfer and store binaries
        # as base64-encoded strings. The base64 string may be provided as a
        # unicode in some circumstances, hence the str() cast here.
        # This str() coercion will only work for pure ASCII unicode strings,
        # on purpose - non base64 data must be passed as a 8bit byte strings.
        if not value:
            return None
        # Detect if the binary content is an SVG for restricting its upload
        # only to system users.
        magic_bytes = {
            b'P',  # first 6 bits of '<' (0x3C) b64 encoded
            b'<',  # plaintext XML tag opening
        }
        if isinstance(value, str):
            value = value.encode()
        if validate and value[:1] in magic_bytes:
            try:
                decoded_value = base64.b64decode(value.translate(None, delete=b'\r\n'), validate=True)
            except binascii.Error:
                decoded_value = value
            # Full mimetype detection
            if (guess_mimetype(decoded_value).startswith('image/svg') and
                    not record.env.is_system()):
                raise UserError(record.env._("Only admins can upload SVG files."))
        if isinstance(value, bytes):
            return psycopg2.Binary(value)
        try:
            return psycopg2.Binary(str(value).encode('ascii'))
        except UnicodeEncodeError:
            raise UserError(record.env._("ASCII characters are required for %(value)s in %(field)s", value=value, field=self.name))