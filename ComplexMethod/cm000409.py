async def confirm_server_link(token: str, user_id: str) -> ConfirmLinkResponse:
    link_token = await PlatformLinkToken.prisma().find_unique(where={"token": token})

    if not link_token:
        raise NotFoundError("Token not found.")
    if link_token.linkType != LinkType.SERVER.value:
        raise LinkFlowMismatchError("This link is for a different linking flow.")
    if link_token.usedAt is not None:
        raise LinkTokenExpiredError("This link has already been used.")
    if link_token.expiresAt.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise LinkTokenExpiredError("This link has expired.")
    if not link_token.platformServerId:
        raise LinkFlowMismatchError("Server token missing server ID.")

    owner = await find_server_link_owner(
        link_token.platform, link_token.platformServerId
    )
    if owner:
        detail = (
            "This server is already linked to your account."
            if owner == user_id
            else "This server is already linked to another AutoGPT account."
        )
        raise LinkAlreadyExistsError(detail)

    # Atomic consume + create so a failed create doesn't burn the token.
    now = datetime.now(timezone.utc)
    try:
        async with transaction() as tx:
            updated = await PlatformLinkToken.prisma(tx).update_many(
                where={"token": token, "usedAt": None, "expiresAt": {"gt": now}},
                data={"usedAt": now},
            )
            if updated == 0:
                raise LinkTokenExpiredError("This link has already been used.")
            await PlatformLink.prisma(tx).create(
                data={
                    "userId": user_id,
                    "platform": link_token.platform,
                    "platformServerId": link_token.platformServerId,
                    "ownerPlatformUserId": link_token.platformUserId,
                    "serverName": link_token.serverName,
                }
            )
    except UniqueViolationError as exc:
        raise LinkAlreadyExistsError(
            "This server was just linked by another request."
        ) from exc

    logger.info(
        "Linked %s server %s to user ...%s",
        link_token.platform,
        link_token.platformServerId,
        user_id[-8:],
    )

    return ConfirmLinkResponse(
        success=True,
        platform=link_token.platform,
        platform_server_id=link_token.platformServerId,
        server_name=link_token.serverName,
    )