    async def create_test_api_keys(self) -> List[Dict[str, Any]]:
        """Create test API keys using the API function."""
        print("Creating test API keys...")

        api_keys = []
        for user in self.users:
            from backend.data.auth.api_key import APIKeyPermission

            try:
                # Use the API function to create API key
                api_key, _ = await create_api_key(
                    name=faker.word(),
                    user_id=user["id"],
                    permissions=[
                        APIKeyPermission.EXECUTE_GRAPH,
                        APIKeyPermission.READ_GRAPH,
                    ],
                    description=faker.text(),
                )
                api_keys.append(api_key.model_dump())
            except Exception as e:
                print(f"Error creating API key for user {user['id']}: {e}")
                continue

        self.api_keys = api_keys
        return api_keys

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

        # Mark about 50% of creators as featured (more for testing)
        num_featured = max(2, int(num_creators * 0.5))
        num_featured = min(
            num_featured, len(selected_profiles)
        )  # Don't exceed available profiles
        featured_profile_ids = set(
            random.sample([p.id for p in selected_profiles], num_featured)
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

        self.profiles = profiles
        return profiles
