async def create_profile(
        self,
        title: str,
        messaging_active: Optional[bool] = None,
        hide_top_header: Optional[bool] = None,
        top_header: Optional[str] = None,
        disable_social: Optional[list[SocialPlatform]] = None,
        team: Optional[bool] = None,
        email: Optional[str] = None,
        sub_header: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> ProfileResponse:
        """
        Create a new User Profile under your Primary Profile.

        Docs: https://www.ayrshare.com/docs/apis/profiles/create-profile

        Args:
            title: Title of the new profile. Must be unique.
            messaging_active: Set to true to activate messaging for this user profile.
            hide_top_header: Hide the top header on the social accounts linkage page.
            top_header: Change the header on the social accounts linkage page.
            disable_social: Array of social networks that are disabled for this user's profile.
            team: Create a new user profile as a team member.
            email: Email address for team member invite (required if team is true).
            sub_header: Change the sub header on the social accounts linkage page.
            tags: Array of strings to tag user profiles.

        Returns:
            ProfileResponse object containing the profile details and profile key.

        Raises:
            AyrshareAPIException: If the API request fails or profile title already exists.
        """
        payload: dict[str, Any] = {
            "title": title,
        }

        if messaging_active is not None:
            payload["messagingActive"] = messaging_active
        if hide_top_header is not None:
            payload["hideTopHeader"] = hide_top_header
        if top_header is not None:
            payload["topHeader"] = top_header
        if disable_social is not None:
            payload["disableSocial"] = [p.value for p in disable_social]
        if team is not None:
            payload["team"] = team
        if email is not None:
            payload["email"] = email
        if sub_header is not None:
            payload["subHeader"] = sub_header
        if tags is not None:
            payload["tags"] = tags

        response = await self._requests.post(self.PROFILES_ENDPOINT, json=payload)

        if not response.ok:
            try:
                error_data = response.json()
                error_message = error_data.get("message", "Unknown error")
            except json.JSONDecodeError:
                error_message = response.text()

            raise AyrshareAPIException(
                f"Ayrshare API request failed ({response.status}): {error_message}",
                response.status,
            )

        response_data = response.json()
        if response_data.get("status") != "success":
            raise AyrshareAPIException(
                f"Ayrshare API returned error: {response_data.get('message', 'Unknown error')}",
                response.status,
            )

        return ProfileResponse(**response_data)