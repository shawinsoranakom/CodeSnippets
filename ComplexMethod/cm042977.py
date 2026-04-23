async def test_profile_creation():
    """Test creating and managing browser profiles."""
    logger.info("Testing profile creation and management", tag="TEST")

    profile_manager = BrowserProfiler(logger=logger)

    try:
        # List existing profiles
        profiles = profile_manager.list_profiles()
        logger.info(f"Found {len(profiles)} existing profiles", tag="TEST")

        # Generate a unique profile name for testing
        test_profile_name = f"test-profile-{uuid.uuid4().hex[:8]}"

        # Create a test profile directory
        profile_path = os.path.join(profile_manager.profiles_dir, test_profile_name)
        os.makedirs(os.path.join(profile_path, "Default"), exist_ok=True)

        # Create a dummy Preferences file to simulate a Chrome profile
        with open(os.path.join(profile_path, "Default", "Preferences"), "w") as f:
            f.write("{\"test\": true}")

        logger.info(f"Created test profile at: {profile_path}", tag="TEST")

        # Verify the profile is now in the list
        profiles = profile_manager.list_profiles()
        profile_found = any(p["name"] == test_profile_name for p in profiles)
        logger.info(f"Profile found in list: {profile_found}", tag="TEST")

        # Try to get the profile path
        retrieved_path = profile_manager.get_profile_path(test_profile_name)
        path_match = retrieved_path == profile_path
        logger.info(f"Retrieved correct profile path: {path_match}", tag="TEST")

        # Delete the profile
        success = profile_manager.delete_profile(test_profile_name)
        logger.info(f"Profile deletion successful: {success}", tag="TEST")

        # Verify it's gone
        profiles_after = profile_manager.list_profiles()
        profile_removed = not any(p["name"] == test_profile_name for p in profiles_after)
        logger.info(f"Profile removed from list: {profile_removed}", tag="TEST")

        # Clean up just in case
        if os.path.exists(profile_path):
            shutil.rmtree(profile_path, ignore_errors=True)

        return profile_found and path_match and success and profile_removed
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", tag="TEST")
        # Clean up test directory
        try:
            if os.path.exists(profile_path):
                shutil.rmtree(profile_path, ignore_errors=True)
        except:
            pass
        return False