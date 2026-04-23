async def set_lock_user(
    matter_client: MatterClient,
    node: MatterNode,
    *,
    user_index: int | None = None,
    user_name: str | None = None,
    user_unique_id: int | None = None,
    user_status: str | None = None,
    user_type: str | None = None,
    credential_rule: str | None = None,
) -> SetLockUserResult:
    """Add or update a user on the lock.

    When user_status, user_type, or credential_rule is None, defaults are used
    for new users and existing values are preserved for modifications.

    Returns typed dict with user_index on success.
    Raises HomeAssistantError on failure.
    """
    lock_endpoint = _get_lock_endpoint_or_raise(node)
    _ensure_usr_support(lock_endpoint)

    if user_index is None:
        # Adding new user - find first available slot
        max_users = (
            lock_endpoint.get_attribute_value(
                None, clusters.DoorLock.Attributes.NumberOfTotalUsersSupported
            )
            or 0
        )

        for idx in range(1, max_users + 1):
            get_user_response = await matter_client.send_device_command(
                node_id=node.node_id,
                endpoint_id=lock_endpoint.endpoint_id,
                command=clusters.DoorLock.Commands.GetUser(userIndex=idx),
            )
            if _get_attr(get_user_response, "userStatus") is None:
                user_index = idx
                break

        if user_index is None:
            raise NoAvailableUserSlotsError("No available user slots on the lock")

        user_status_enum = (
            USER_STATUS_REVERSE_MAP.get(
                user_status,
                clusters.DoorLock.Enums.UserStatusEnum.kOccupiedEnabled,
            )
            if user_status is not None
            else clusters.DoorLock.Enums.UserStatusEnum.kOccupiedEnabled
        )

        await matter_client.send_device_command(
            node_id=node.node_id,
            endpoint_id=lock_endpoint.endpoint_id,
            command=clusters.DoorLock.Commands.SetUser(
                operationType=clusters.DoorLock.Enums.DataOperationTypeEnum.kAdd,
                userIndex=user_index,
                userName=user_name,
                userUniqueID=user_unique_id,
                userStatus=user_status_enum,
                userType=USER_TYPE_REVERSE_MAP.get(
                    user_type,
                    clusters.DoorLock.Enums.UserTypeEnum.kUnrestrictedUser,
                )
                if user_type is not None
                else clusters.DoorLock.Enums.UserTypeEnum.kUnrestrictedUser,
                credentialRule=CREDENTIAL_RULE_REVERSE_MAP.get(
                    credential_rule,
                    clusters.DoorLock.Enums.CredentialRuleEnum.kSingle,
                )
                if credential_rule is not None
                else clusters.DoorLock.Enums.CredentialRuleEnum.kSingle,
            ),
            timed_request_timeout_ms=LOCK_TIMED_REQUEST_TIMEOUT_MS,
        )
    else:
        # Updating existing user - preserve existing values when not specified
        get_user_response = await matter_client.send_device_command(
            node_id=node.node_id,
            endpoint_id=lock_endpoint.endpoint_id,
            command=clusters.DoorLock.Commands.GetUser(userIndex=user_index),
        )

        if _get_attr(get_user_response, "userStatus") is None:
            raise UserSlotEmptyError(f"User slot {user_index} is empty")

        resolved_user_name = (
            user_name
            if user_name is not None
            else _get_attr(get_user_response, "userName")
        )
        resolved_unique_id = (
            user_unique_id
            if user_unique_id is not None
            else _get_attr(get_user_response, "userUniqueID")
        )

        resolved_status = (
            USER_STATUS_REVERSE_MAP[user_status]
            if user_status is not None
            else _get_attr(get_user_response, "userStatus")
        )

        resolved_type = (
            USER_TYPE_REVERSE_MAP[user_type]
            if user_type is not None
            else _get_attr(get_user_response, "userType")
        )

        resolved_rule = (
            CREDENTIAL_RULE_REVERSE_MAP[credential_rule]
            if credential_rule is not None
            else _get_attr(get_user_response, "credentialRule")
        )

        await matter_client.send_device_command(
            node_id=node.node_id,
            endpoint_id=lock_endpoint.endpoint_id,
            command=clusters.DoorLock.Commands.SetUser(
                operationType=clusters.DoorLock.Enums.DataOperationTypeEnum.kModify,
                userIndex=user_index,
                userName=resolved_user_name,
                userUniqueID=resolved_unique_id,
                userStatus=resolved_status,
                userType=resolved_type,
                credentialRule=resolved_rule,
            ),
            timed_request_timeout_ms=LOCK_TIMED_REQUEST_TIMEOUT_MS,
        )

    return SetLockUserResult(user_index=user_index)