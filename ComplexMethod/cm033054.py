def _get_all_user_emails(self) -> list[str]:
        if self._specific_user_emails:
            return self._specific_user_emails

        # Start with primary admin email
        user_emails = [self.primary_admin_email]

        # Only fetch additional users if using service account
        if isinstance(self.creds, OAuthCredentials):
            return user_emails

        admin_service = get_admin_service(
            creds=self.creds,
            user_email=self.primary_admin_email,
        )

        # Get admins first since they're more likely to have access to most files
        for is_admin in [True, False]:
            query = "isAdmin=true" if is_admin else "isAdmin=false"
            for user in execute_paginated_retrieval(
                retrieval_function=admin_service.users().list,
                list_key="users",
                fields=USER_FIELDS,
                domain=self.google_domain,
                query=query,
            ):
                if email := user.get("primaryEmail"):
                    if email not in user_emails:
                        user_emails.append(email)
        return user_emails