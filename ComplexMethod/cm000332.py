async def update_test_profiles(self) -> List[Dict[str, Any]]:
        """Update existing user profiles to make some into featured creators."""
        print("Updating user profiles to create featured creators...")

        # Get all existing profiles (auto-created when users were created)
        existing_profiles = await prisma.profile.find_many(
            where={"userId": {"in": [user["id"] for user in self.users]}}
        )

        if not existing_profiles:
            print("No existing profiles found. Profiles may not be auto-created.")
            return []

        profiles = []
        # Select about 70% of users to become creators (update their profiles)
        num_creators = max(1, int(len(existing_profiles) * 0.7))
        selected_profiles = random.sample(
            existing_profiles, min(num_creators, len(existing_profiles))
        )

        # Guarantee at least GUARANTEED_FEATURED_CREATORS featured creators
        num_featured = max(GUARANTEED_FEATURED_CREATORS, int(num_creators * 0.5))
        num_featured = min(
            num_featured, len(selected_profiles)
        )  # Don't exceed available profiles
        featured_profile_ids = set(
            random.sample([p.id for p in selected_profiles], num_featured)
        )
        print(
            f"🎯 Creating {num_featured} featured creators (min: {GUARANTEED_FEATURED_CREATORS})"
        )

        for profile in selected_profiles:
            try:
                is_featured = profile.id in featured_profile_ids

                # Update the profile with creator data
                updated_profile = await prisma.profile.update(
                    where={"id": profile.id},
                    data={
                        "name": faker.name(),
                        "username": faker.user_name()
                        + str(random.randint(100, 999)),  # Ensure uniqueness
                        "description": faker.text(max_nb_chars=200),
                        "links": [faker.url() for _ in range(random.randint(1, 3))],
                        "avatarUrl": get_image(),
                        "isFeatured": is_featured,
                    },
                )

                if updated_profile:
                    profiles.append(updated_profile.model_dump())

            except Exception as e:
                print(f"Error updating profile {profile.id}: {e}")
                continue

        deterministic_creator = next(
            (
                user
                for user in self.users
                if user["email"] == E2E_MARKETPLACE_CREATOR_EMAIL
            ),
            None,
        )
        if deterministic_creator:
            deterministic_profile = next(
                (
                    profile
                    for profile in existing_profiles
                    if profile.userId == deterministic_creator["id"]
                ),
                None,
            )
            if deterministic_profile:
                try:
                    updated_profile = await prisma.profile.update(
                        where={"id": deterministic_profile.id},
                        data={
                            "name": "E2E Marketplace Creator",
                            "username": E2E_MARKETPLACE_CREATOR_USERNAME,
                            "description": "Deterministic marketplace creator for Playwright PR E2E coverage.",
                            "links": ["https://example.com/e2e-marketplace"],
                            "avatarUrl": get_image(),
                            "isFeatured": True,
                        },
                    )
                    profiles = [
                        profile
                        for profile in profiles
                        if profile.get("id") != deterministic_profile.id
                    ]
                    if updated_profile is not None:
                        profiles.append(updated_profile.model_dump())
                except Exception as e:
                    print(f"Error updating deterministic E2E creator profile: {e}")

        self.profiles = profiles
        return profiles