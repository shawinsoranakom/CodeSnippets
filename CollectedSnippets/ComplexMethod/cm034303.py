def default(self, o: _t.Any) -> _t.Any:
        """Hooked default that can conditionally bypass base encoder behavior based on this instance's config."""
        if type(o) is _profiles._WrappedValue:  # pylint: disable=unidiomatic-typecheck
            o = o.wrapped

        if not self._preprocess_unsafe and type(o) is _legacy._Untrusted:  # pylint: disable=unidiomatic-typecheck
            return o.value  # if not emitting unsafe markers, bypass custom unsafe serialization and just return the raw value

        if self._vault_to_text and type(o) is _vault.EncryptedString:  # pylint: disable=unidiomatic-typecheck
            return str(o)  # decrypt and return the plaintext (or fail trying)

        if self._decode_bytes and isinstance(o, bytes):
            return o.decode(errors='surrogateescape')  # backward compatibility with `ansible.module_utils.basic.jsonify`

        return super().default(o)