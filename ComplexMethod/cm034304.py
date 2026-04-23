def _visit[T](self, key: t.Any, value: T) -> T:
        """Internal implementation to recursively visit a data structure's contents."""
        self._current = key  # supports StateTrackingMixIn

        value_type: type = type(value)

        # handle EncryptedString conversion before more generic transformation and native conversions
        if value_type is EncryptedString:  # pylint: disable=unidiomatic-typecheck
            match self.encrypted_string_behavior:
                case EncryptedStringBehavior.DECRYPT:
                    value = str(value)  # type: ignore[assignment]
                    value_type = str
                case EncryptedStringBehavior.REDACT:
                    value = "<redacted>"  # type: ignore[assignment]
                    value_type = str
                case EncryptedStringBehavior.FAIL:
                    raise AnsibleVariableTypeError.from_value(obj=value)
        elif self.apply_transforms and value_type in _transform._type_transform_mapping:
            value = self._template_engine.transform(value)
            value_type = type(value)

        if self.convert_to_native_values and isinstance(value, _datatag.AnsibleTaggedObject):
            value = value._native_copy()
            value_type = type(value)

        result: T

        # DTFIX-FUTURE: Visitor generally ignores dict/mapping keys by default except for debugging and schema-aware checking.
        #               It could be checking keys destined for variable storage to apply more strict rules about key shape and type.

        if (result := self._early_visit(value, value_type)) is not _sentinel:
            pass
        # DTFIX7: de-duplicate and optimize; extract inline generator expressions and fallback function or mapping for native type calculation?
        elif value_type in _ANSIBLE_ALLOWED_MAPPING_VAR_TYPES:  # check mappings first, because they're also collections
            with self:  # supports StateTrackingMixIn
                result = AnsibleTagHelper.tag_copy(value, ((self._visit_key(k), self._visit(k, v)) for k, v in value.items()), value_type=value_type)
        elif value_type in _ANSIBLE_ALLOWED_NON_SCALAR_COLLECTION_VAR_TYPES:
            with self:  # supports StateTrackingMixIn
                result = AnsibleTagHelper.tag_copy(value, (self._visit(k, v) for k, v in enumerate(t.cast(t.Iterable, value))), value_type=value_type)
        elif self.convert_mapping_to_dict and _internal.is_intermediate_mapping(value):
            with self:  # supports StateTrackingMixIn
                result = {self._visit_key(k): self._visit(k, v) for k, v in value.items()}  # type: ignore[assignment]
        elif self.convert_sequence_to_list and _internal.is_intermediate_iterable(value):
            with self:  # supports StateTrackingMixIn
                result = [self._visit(k, v) for k, v in enumerate(t.cast(t.Iterable, value))]  # type: ignore[assignment]
        elif self.convert_custom_scalars and isinstance(value, str):
            result = str(value)  # type: ignore[assignment]
        elif self.convert_custom_scalars and isinstance(value, float):
            result = float(value)  # type: ignore[assignment]
        elif self.convert_custom_scalars and isinstance(value, int) and not isinstance(value, bool):
            result = int(value)  # type: ignore[assignment]
        elif value_type in _ANSIBLE_ALLOWED_VAR_TYPES:
            # supported scalar type that requires no special handling, just return as-is
            result = value
        elif self.encrypted_string_behavior is EncryptedStringBehavior.PRESERVE and isinstance(value, EncryptedString):
            result = value  # type: ignore[assignment]
        else:
            raise AnsibleVariableTypeError.from_value(obj=value)

        if self.origin and not Origin.is_tagged_on(result):
            # apply shared instance default origin tag
            result = self.origin.tag(result)

        return result