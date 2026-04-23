def _find_duplicate_in_users(
        self, users: dict[str, dict], base_email: str, current_user_id: str
    ) -> bool:
        """Check if any user in the provided list matches the base email pattern.

        Filters users to find duplicates that match the base email pattern,
        excluding the current user.

        Args:
            users: Dictionary mapping user IDs to user objects
            base_email: The base email to match against
            current_user_id: The user ID to exclude from the check

        Returns:
            True if a duplicate is found, False otherwise
        """
        regex_pattern = get_base_email_regex_pattern(base_email)
        if not regex_pattern:
            logger.warning(
                f'Could not generate regex pattern for base email: {base_email}'
            )
            # Fallback to simple matching
            for user in users.values():
                user_email = user.get('email', '').lower()
                if (
                    user_email
                    and user.get('id') != current_user_id
                    and matches_base_email(user_email, base_email)
                ):
                    logger.info(
                        f'Found duplicate email: {user_email} matches base {base_email}'
                    )
                    return True
        else:
            for user in users.values():
                user_email = user.get('email', '')
                if (
                    user_email
                    and user.get('id') != current_user_id
                    and regex_pattern.match(user_email)
                ):
                    logger.info(
                        f'Found duplicate email: {user_email} matches base {base_email}'
                    )
                    return True

        return False