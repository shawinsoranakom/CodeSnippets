def _to_boto_request_value(self, request_value: Any, value_shape: Shape) -> Any:
        boto_request_value = request_value
        if isinstance(value_shape, StructureShape):
            self._to_boto_request(request_value, value_shape)
        elif isinstance(value_shape, ListShape) and isinstance(request_value, list):
            for request_list_value in request_value:
                self._to_boto_request_value(request_list_value, value_shape.member)  # noqa
        elif isinstance(value_shape, StringShape) and not isinstance(request_value, str):
            boto_request_value = to_json_str(request_value)
        elif value_shape.type_name == "blob" and not isinstance(boto_request_value, bytes):
            boto_request_value = to_json_str(request_value, separators=(",", ":"))
            boto_request_value = to_bytes(boto_request_value)
        return boto_request_value