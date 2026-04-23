def list_profiles(self) -> List[Dict[str, Any]]:
        """
        Lists all available browser profiles in the Crawl4AI profiles directory.

        Returns:
            list: A list of dictionaries containing profile information:
                  [{"name": "profile_name", "path": "/path/to/profile", "created": datetime, "type": "chromium|firefox"}]

        Example:
            ```python
            profiler = BrowserProfiler()

            # List all available profiles
            profiles = profiler.list_profiles()

            for profile in profiles:
                print(f"Profile: {profile['name']}")
                print(f"  Path: {profile['path']}")
                print(f"  Created: {profile['created']}")
                print(f"  Browser type: {profile['type']}")
            ```
        """
        if not os.path.exists(self.profiles_dir):
            return []

        profiles = []

        for name in os.listdir(self.profiles_dir):
            profile_path = os.path.join(self.profiles_dir, name)

            # Skip if not a directory
            if not os.path.isdir(profile_path):
                continue

            # Check if this looks like a valid browser profile
            # For Chromium: Look for Preferences file
            # For Firefox: Look for prefs.js file
            is_valid = False

            if os.path.exists(os.path.join(profile_path, "Preferences")) or \
               os.path.exists(os.path.join(profile_path, "Default", "Preferences")):
                is_valid = "chromium"
            elif os.path.exists(os.path.join(profile_path, "prefs.js")):
                is_valid = "firefox"

            if is_valid:
                # Get creation time
                created = datetime.datetime.fromtimestamp(
                    os.path.getctime(profile_path)
                )

                profiles.append({
                    "name": name,
                    "path": profile_path,
                    "created": created,
                    "type": is_valid
                })

        # Sort by creation time, newest first
        profiles.sort(key=lambda x: x["created"], reverse=True)

        return profiles