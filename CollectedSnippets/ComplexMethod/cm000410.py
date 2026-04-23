async def confirm_user_link(token: str, user_id: str) -> ConfirmUserLinkResponse:
    link_token = await PlatformLinkToken.prisma().find_unique(where={"token": token})

    if not link_token:
        raise NotFoundError("Token not found.")
    if link_token.linkType != LinkType.USER.value:
        raise LinkFlowMismatchError("This link is for a different linking flow.")
    if link_token.usedAt is not None:
        raise LinkTokenExpiredError("This link has already been used.")
    if link_token.expiresAt.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise LinkTokenExpiredError("This link has expired.")

    owner = await find_user_link_owner(link_token.platform, link_token.platformUserId)
    if owner:
        detail = (
            "Your DMs are already linked to your account."
            if owner == user_id
            else "This platform user is already linked to another AutoGPT account."
        )
        raise LinkAlreadyExistsError(detail)

    now = datetime.now(timezone.utc)
    try:
        async with transaction() as tx:
            updated = await PlatformLinkToken.prisma(tx).update_many(
                where={"token": token, "usedAt": None, "expiresAt": {"gt": now}},
                data={"usedAt": now},
            )
            if updated == 0:
                raise LinkTokenExpiredError("This link has already been used.")
            await PlatformUserLink.prisma(tx).create(
                data={
                    "userId": user_id,
                    "platform": link_token.platform,
                    "platformUserId": link_token.platformUserId,
                    "platformUsername": link_token.platformUsername,
                }
            )
    except UniqueViolationError as exc:
        raise LinkAlreadyExistsError(
            "Your DMs were just linked by another request."
        ) from exc

    logger.info(
        "Linked %s DMs to AutoGPT user ...%s", link_token.platform, user_id[-8:]
    )

    return ConfirmUserLinkResponse(
        success=True,
        platform=link_token.platform,
        platform_user_id=link_token.platformUserId,
    )