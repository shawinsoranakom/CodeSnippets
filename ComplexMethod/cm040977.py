def import_key_material(
        self,
        context: RequestContext,
        key_id: KeyIdType,
        import_token: CiphertextType,
        encrypted_key_material: CiphertextType,
        valid_to: DateType | None = None,
        expiration_model: ExpirationModelType | None = None,
        import_type: ImportType | None = None,
        key_material_description: KeyMaterialDescriptionType | None = None,
        key_material_id: BackingKeyIdType | None = None,
        **kwargs,
    ) -> ImportKeyMaterialResponse:
        store = self._get_store(context.account_id, context.region)
        import_token = to_str(import_token)
        import_state = store.imports.get(import_token)
        if not import_state:
            raise NotFoundException(f"Unable to find key import token '{import_token}'")
        key_to_import_material_to = self._get_kms_key(
            context.account_id,
            context.region,
            key_id,
            enabled_key_allowed=True,
            disabled_key_allowed=True,
        )

        # TODO check if there was already a key imported for this kms key
        # if so, it has to be identical. We cannot change keys by reimporting after deletion/expiry
        key_material = self._decrypt_wrapped_key_material(import_state, encrypted_key_material)
        key_material_id = key_to_import_material_to.generate_key_material_id(key_material)
        key_to_import_material_to.metadata["ExpirationModel"] = (
            expiration_model or ExpirationModelType.KEY_MATERIAL_EXPIRES
        )
        if (
            key_to_import_material_to.metadata["ExpirationModel"]
            == ExpirationModelType.KEY_MATERIAL_EXPIRES
            and not valid_to
        ):
            raise ValidationException(
                "A validTo date must be set if the ExpirationModel is KEY_MATERIAL_EXPIRES"
            )
        if existing_pending_material := key_to_import_material_to.crypto_key.pending_key_material:
            pending_key_material_id = key_to_import_material_to.generate_key_material_id(
                existing_pending_material
            )
            raise KMSInvalidStateException(
                f"New key material (id: {key_material_id}) cannot be imported into KMS key "
                f"{key_to_import_material_to.metadata['Arn']}, because another key material "
                f"(id: {pending_key_material_id}) is pending rotation."
            )

        # TODO actually set validTo and make the key expire
        key_to_import_material_to.metadata["Enabled"] = True
        key_to_import_material_to.metadata["KeyState"] = KeyState.Enabled
        key_to_import_material_to.crypto_key.load_key_material(key_material)

        # KeyMaterialId / CurrentKeyMaterialId is only exposed for symmetric encryption keys.
        key_material_id_response = None
        if key_to_import_material_to.metadata["KeySpec"] == KeySpec.SYMMETRIC_DEFAULT:
            key_material_id_response = key_to_import_material_to.generate_key_material_id(
                key_material
            )

            # If there is no CurrentKeyMaterialId, instantly promote the pending key material to the current.
            if key_to_import_material_to.metadata.get("CurrentKeyMaterialId") is None:
                key_to_import_material_to.metadata["CurrentKeyMaterialId"] = (
                    key_material_id_response
                )
                key_to_import_material_to.crypto_key.key_material = (
                    key_to_import_material_to.crypto_key.pending_key_material
                )
                key_to_import_material_to.crypto_key.pending_key_material = None

        return ImportKeyMaterialResponse(
            KeyId=key_to_import_material_to.metadata["Arn"],
            KeyMaterialId=key_material_id_response,
        )