async def update_profile(
    user_id: str, profile: store_model.Profile
) -> store_model.ProfileDetails:
    """
    Update the store profile for a user or create a new one if it doesn't exist.
    Args:
        user_id: ID of the authenticated user
        profile: Updated profile details
    Returns:
        ProfileDetails: The updated or created profile details
    Raises:
        DatabaseError: If there's an issue updating or creating the profile
    """
    logger.info(f"Updating profile for user {user_id} with data: {profile}")
    try:
        # Sanitize username to allow only letters, numbers, and hyphens
        username = "".join(
            c if c.isalpha() or c == "-" or c.isnumeric() else ""
            for c in profile.username
        ).lower()
        # Check if profile exists for the given user_id
        existing_profile = await prisma.models.Profile.prisma().find_first(
            where={"userId": user_id}
        )
        if not existing_profile:
            raise store_exceptions.ProfileNotFoundError(
                f"Profile not found for user {user_id}. This should not be possible."
            )

        # Verify that the user is authorized to update this profile
        if existing_profile.userId != user_id:
            logger.error(
                f"Unauthorized update attempt for profile {existing_profile.id} "
                f"by user {user_id}"
            )
            raise DatabaseError(
                f"Unauthorized update attempt for profile {existing_profile.id} "
                f"by user {user_id}"
            )

        logger.debug(f"Updating existing profile for user {user_id}")
        # Prepare update data, only including non-None values
        update_data = {}
        if profile.name is not None:
            update_data["name"] = profile.name
        if profile.username is not None:
            update_data["username"] = username
        if profile.description is not None:
            update_data["description"] = profile.description
        if profile.links is not None:
            update_data["links"] = profile.links
        if profile.avatar_url is not None:
            update_data["avatarUrl"] = profile.avatar_url

        # Update the existing profile
        updated_profile = await prisma.models.Profile.prisma().update(
            where={"id": existing_profile.id},
            data=prisma.types.ProfileUpdateInput(**update_data),
        )
        if updated_profile is None:
            logger.error(f"Failed to update profile for user {user_id}")
            raise DatabaseError("Failed to update profile")

        return store_model.ProfileDetails.from_db(updated_profile)

    except prisma.errors.PrismaError as e:
        logger.error(f"Database error updating profile: {e}")
        raise DatabaseError("Failed to update profile") from e