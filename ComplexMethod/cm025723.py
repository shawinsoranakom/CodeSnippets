async def set_lock_credential(
    matter_client: MatterClient,
    node: MatterNode,
    *,
    credential_type: str,
    credential_data: str,
    credential_index: int | None = None,
    user_index: int | None = None,
    user_status: str | None = None,
    user_type: str | None = None,
) -> SetLockCredentialResult:
    """Add or modify a credential on the lock.

    Returns typed dict with credential_index, user_index, and next_credential_index.
    Raises ServiceValidationError for validation failures.
    Raises HomeAssistantError for device communication failures.
    """
    lock_endpoint = _get_lock_endpoint_or_raise(node)
    _ensure_usr_support(lock_endpoint)
    _validate_credential_type_support(lock_endpoint, credential_type)
    _validate_credential_data(lock_endpoint, credential_type, credential_data)

    cred_type_int = CREDENTIAL_TYPE_REVERSE_MAP[credential_type]
    cred_data_bytes = _credential_data_to_bytes(credential_type, credential_data)

    # Determine operation type and credential index
    operation_type = clusters.DoorLock.Enums.DataOperationTypeEnum.kAdd

    if credential_index is None:
        # Auto-find first available credential slot.
        # Use the credential-type-specific capacity as the upper bound.
        max_creds_attr = _CREDENTIAL_TYPE_CAPACITY_ATTR.get(
            credential_type,
            clusters.DoorLock.Attributes.NumberOfTotalUsersSupported,
        )
        max_creds_raw = lock_endpoint.get_attribute_value(None, max_creds_attr)
        max_creds = (
            max_creds_raw if isinstance(max_creds_raw, int) and max_creds_raw > 0 else 5
        )
        for idx in range(1, max_creds + 1):
            status_response = await matter_client.send_device_command(
                node_id=node.node_id,
                endpoint_id=lock_endpoint.endpoint_id,
                command=clusters.DoorLock.Commands.GetCredentialStatus(
                    credential=clusters.DoorLock.Structs.CredentialStruct(
                        credentialType=cred_type_int,
                        credentialIndex=idx,
                    ),
                ),
            )
            if not _get_attr(status_response, "credentialExists"):
                credential_index = idx
                break

        if credential_index is None:
            raise NoAvailableUserSlotsError("No available credential slots on the lock")
    else:
        # Check if slot is occupied to determine Add vs Modify
        status_response = await matter_client.send_device_command(
            node_id=node.node_id,
            endpoint_id=lock_endpoint.endpoint_id,
            command=clusters.DoorLock.Commands.GetCredentialStatus(
                credential=clusters.DoorLock.Structs.CredentialStruct(
                    credentialType=cred_type_int,
                    credentialIndex=credential_index,
                ),
            ),
        )
        if _get_attr(status_response, "credentialExists"):
            operation_type = clusters.DoorLock.Enums.DataOperationTypeEnum.kModify

    # Resolve optional user_status and user_type enums
    resolved_user_status = (
        USER_STATUS_REVERSE_MAP.get(user_status) if user_status is not None else None
    )
    resolved_user_type = (
        USER_TYPE_REVERSE_MAP.get(user_type) if user_type is not None else None
    )

    set_cred_response = await matter_client.send_device_command(
        node_id=node.node_id,
        endpoint_id=lock_endpoint.endpoint_id,
        command=clusters.DoorLock.Commands.SetCredential(
            operationType=operation_type,
            credential=clusters.DoorLock.Structs.CredentialStruct(
                credentialType=cred_type_int,
                credentialIndex=credential_index,
            ),
            credentialData=cred_data_bytes,
            userIndex=user_index,
            userStatus=resolved_user_status,
            userType=resolved_user_type,
        ),
        timed_request_timeout_ms=LOCK_TIMED_REQUEST_TIMEOUT_MS,
    )

    status_code = _get_attr(set_cred_response, "status")
    status_str = SET_CREDENTIAL_STATUS_MAP.get(status_code, f"unknown({status_code})")
    if status_str != "success":
        raise SetCredentialFailedError(
            translation_domain="matter",
            translation_key="set_credential_failed",
            translation_placeholders={"status": status_str},
        )

    return SetLockCredentialResult(
        credential_index=credential_index,
        user_index=_get_attr(set_cred_response, "userIndex"),
        next_credential_index=_get_attr(set_cred_response, "nextCredentialIndex"),
    )