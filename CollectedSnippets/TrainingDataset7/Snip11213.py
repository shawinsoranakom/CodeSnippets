def value_to_string(self, obj):
        """Binary data is serialized as base64"""
        return b64encode(self.value_from_object(obj)).decode("ascii")