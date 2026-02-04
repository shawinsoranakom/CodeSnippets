async def create_test_users(self) -> List[Dict[str, Any]]:
        """Create test users using Supabase client."""
        print(f"Creating {NUM_USERS} test users...")

        supabase = get_supabase()
        users = []

        for i in range(NUM_USERS):
            try:
                # Generate test user data
                if i == 0:
                    # First user should have test123@gmail.com email for testing
                    email = "test123@gmail.com"
                else:
                    email = faker.unique.email()
                password = "testpassword123"  # Standard test password
                user_id = f"test-user-{i}-{faker.uuid4()}"

                # Create user in Supabase Auth (if needed)
                try:
                    auth_response = supabase.auth.admin.create_user(
                        {"email": email, "password": password, "email_confirm": True}
                    )
                    if auth_response.user:
                        user_id = auth_response.user.id
                except Exception as supabase_error:
                    print(
                        f"Supabase user creation failed for {email}, using fallback: {supabase_error}"
                    )
                    # Fall back to direct database creation

                # Create mock user data similar to what auth middleware would provide
                user_data = {
                    "sub": user_id,
                    "email": email,
                }

                # Use the API function to create user in local database
                user = await get_or_create_user(user_data)
                users.append(user.model_dump())

            except Exception as e:
                print(f"Error creating user {i}: {e}")
                continue

        self.users = users
        return users
