async def create_user_and_profile(db: Prisma) -> None:
    """Create the autogpt user and profile if they don't exist."""
    # Check if user exists
    existing_user = await db.user.find_unique(where={"id": AUTOGPT_USER_ID})
    if existing_user:
        print(f"User {AUTOGPT_USER_ID} already exists, skipping user creation")
    else:
        print(f"Creating user {AUTOGPT_USER_ID}")
        await db.user.create(
            data=UserCreateInput(
                id=AUTOGPT_USER_ID,
                email=AUTOGPT_EMAIL,
                name="AutoGPT",
                metadata=Json({}),
                integrations="",
            )
        )

    # Check if profile exists
    existing_profile = await db.profile.find_first(where={"userId": AUTOGPT_USER_ID})
    if existing_profile:
        print(
            f"Profile for user {AUTOGPT_USER_ID} already exists, skipping profile creation"
        )
    else:
        print(f"Creating profile for user {AUTOGPT_USER_ID}")
        await db.profile.create(
            data=ProfileCreateInput(
                userId=AUTOGPT_USER_ID,
                name="AutoGPT",
                username=AUTOGPT_USERNAME,
                description="Official AutoGPT agents and templates",
                links=["https://agpt.co"],
                avatarUrl="https://storage.googleapis.com/agpt-prod-website-artifacts/users/b3e41ea4-2f4c-4964-927c-fe682d857bad/images/4b5781a6-49e1-433c-9a75-65af1be5c02d.png",
            )
        )
