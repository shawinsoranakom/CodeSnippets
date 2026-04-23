def _get_key_id_from_any_id(account_id: str, region_name: str, some_id: str) -> str:
        """
        Resolve a KMS key ID by using one of the following identifiers:
        - key ID
        - key ARN
        - key alias
        - key alias ARN
        """
        alias_name = None
        key_id = None
        key_arn = None

        if some_id.startswith("arn:"):
            if ":alias/" in some_id:
                alias_arn = some_id
                alias_name = "alias/" + alias_arn.split(":alias/")[1]
            elif ":key/" in some_id:
                key_arn = some_id
                key_id = key_arn.split(":key/")[1]
                parsed_arn = parse_arn(key_arn)
                if parsed_arn["region"] != region_name:
                    raise NotFoundException(f"Invalid arn {parsed_arn['region']}")
            else:
                raise ValueError(
                    f"Supplied value of {some_id} is an ARN, but neither of a KMS key nor of a KMS key "
                    f"alias"
                )
        elif some_id.startswith("alias/"):
            alias_name = some_id
        else:
            key_id = some_id

        store = kms_stores[account_id][region_name]

        if alias_name:
            KmsProvider._create_alias_if_reserved_and_not_exists(
                account_id,
                region_name,
                alias_name,
            )
            if alias_name not in store.aliases:
                raise NotFoundException(f"Unable to find KMS alias with name {alias_name}")
            key_id = store.aliases[alias_name].metadata["TargetKeyId"]

        # regular KeyId are UUID, and MultiRegion keys starts with 'mrk-' and 32 hex chars
        if not PATTERN_UUID.match(key_id) and not MULTI_REGION_PATTERN.match(key_id):
            raise NotFoundException(f"Invalid keyId '{key_id}'")

        if key_id not in store.keys:
            if not key_arn:
                key_arn = (
                    f"arn:{get_partition(region_name)}:kms:{region_name}:{account_id}:key/{key_id}"
                )
            raise NotFoundException(f"Key '{key_arn}' does not exist")

        return key_id