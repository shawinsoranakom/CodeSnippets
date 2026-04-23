def _encode_parts(self, messages, encode_empty=False):
        """
        Return an encoded version of the serialized messages list which can be
        stored as plain text.

        Since the data will be retrieved from the client-side, the encoded data
        also contains a hash to ensure that the data was not tampered with.
        """
        if messages or encode_empty:
            return self.signer.sign_object(
                messages, serializer=MessagePartGatherSerializer, compress=True
            )