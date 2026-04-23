def _populate_metadata(
        self,
        create_key_request: CreateKeyRequest,
        account_id: str,
        region: str,
        custom_key_id: str | None = None,
    ) -> None:
        self.metadata = KeyMetadata()
        # Metadata fields coming from a creation request
        #
        # We do not include tags into the metadata. Tags might be present in a key creation request, but our metadata
        # only contains data displayed by DescribeKey. And tags are not there:
        # https://docs.aws.amazon.com/kms/latest/APIReference/API_DescribeKey.html
        # "DescribeKey does not return the following information: ... Tags on the KMS key."

        self.metadata["Description"] = create_key_request.get("Description") or ""
        self.metadata["MultiRegion"] = create_key_request.get("MultiRegion") or False
        self.metadata["Origin"] = create_key_request.get("Origin") or "AWS_KMS"
        # https://docs.aws.amazon.com/kms/latest/APIReference/API_CreateKey.html#KMS-CreateKey-request-CustomerMasterKeySpec
        # CustomerMasterKeySpec has been deprecated, still used for compatibility. Is replaced by KeySpec.
        # The meaning is the same, just the name differs.
        self.metadata["KeySpec"] = (
            create_key_request.get("KeySpec")
            or create_key_request.get("CustomerMasterKeySpec")
            or "SYMMETRIC_DEFAULT"
        )
        self.metadata["CustomerMasterKeySpec"] = self.metadata.get("KeySpec")
        self.metadata["KeyUsage"] = self._get_key_usage(
            create_key_request.get("KeyUsage"), self.metadata.get("KeySpec")
        )

        # Metadata fields AWS introduces automatically
        self.metadata["AWSAccountId"] = account_id
        self.metadata["CreationDate"] = datetime.datetime.now()
        self.metadata["Enabled"] = create_key_request.get("Origin") != OriginType.EXTERNAL
        self.metadata["KeyManager"] = "CUSTOMER"
        self.metadata["KeyState"] = (
            KeyState.Enabled
            if create_key_request.get("Origin") != OriginType.EXTERNAL
            else KeyState.PendingImport
        )

        if custom_key_id:
            self.metadata["KeyId"] = custom_key_id
        elif self.metadata.get("MultiRegion"):
            # https://docs.aws.amazon.com/kms/latest/developerguide/multi-region-keys-overview.html
            # "Notice that multi-Region keys have a distinctive key ID that begins with mrk-. You can use the mrk- prefix to
            # identify MRKs programmatically."
            # The ID for MultiRegion keys also do not have dashes.
            self.metadata["KeyId"] = "mrk-" + str(uuid.uuid4().hex)
        else:
            self.metadata["KeyId"] = str(uuid.uuid4())
        self.calculate_and_set_arn(account_id, region)

        self._populate_encryption_algorithms(
            self.metadata.get("KeyUsage"), self.metadata.get("KeySpec")
        )
        self._populate_signing_algorithms(
            self.metadata.get("KeyUsage"), self.metadata.get("KeySpec")
        )
        self._populate_mac_algorithms(self.metadata.get("KeyUsage"), self.metadata.get("KeySpec"))

        if self.metadata["MultiRegion"]:
            self.metadata["MultiRegionConfiguration"] = MultiRegionConfiguration(
                MultiRegionKeyType=MultiRegionKeyType.PRIMARY,
                PrimaryKey=MultiRegionKey(Arn=self.metadata["Arn"], Region=region),
                ReplicaKeys=[],
            )