def sign_object(self, obj, serializer=JSONSerializer, compress=False):
        """
        Return URL-safe, hmac signed base64 compressed JSON string.

        If compress is True (not the default), check if compressing using zlib
        can save some space. Prepend a '.' to signify compression. This is
        included in the signature, to protect against zip bombs.

        The serializer is expected to return a bytestring.
        """
        data = serializer().dumps(obj)
        # Flag for if it's been compressed or not.
        is_compressed = False

        if compress:
            # Avoid zlib dependency unless compress is being used.
            compressed = zlib.compress(data)
            if len(compressed) < (len(data) - 1):
                data = compressed
                is_compressed = True
        base64d = b64_encode(data).decode()
        if is_compressed:
            base64d = "." + base64d
        return self.sign(base64d)