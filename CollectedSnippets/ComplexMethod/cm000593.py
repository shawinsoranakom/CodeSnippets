async def run(
        self,
        input_data: "PostToBlueskyBlock.Input",
        *,
        user_id: str,
        **kwargs,
    ) -> BlockOutput:
        """Post to Bluesky with Bluesky-specific options."""

        profile_key = await get_profile_key(user_id)
        if not profile_key:
            yield "error", "Please link a social account via Ayrshare"
            return

        client = create_ayrshare_client()
        if not client:
            yield "error", "Ayrshare integration is not configured. Please set up the AYRSHARE_API_KEY."
            return

        # Validate character limit for Bluesky
        if len(input_data.post) > 300:
            yield "error", f"Post text exceeds Bluesky's 300 character limit ({len(input_data.post)} characters)"
            return

        # Validate media constraints for Bluesky
        if len(input_data.media_urls) > 4:
            yield "error", "Bluesky supports a maximum of 4 images or 1 video"
            return

        # Convert datetime to ISO format if provided
        iso_date = (
            input_data.schedule_date.isoformat() if input_data.schedule_date else None
        )

        # Build Bluesky-specific options
        bluesky_options = {}
        if input_data.alt_text:
            bluesky_options["altText"] = input_data.alt_text

        response = await client.create_post(
            post=input_data.post,
            platforms=[SocialPlatform.BLUESKY],
            media_urls=input_data.media_urls,
            is_video=input_data.is_video,
            schedule_date=iso_date,
            disable_comments=input_data.disable_comments,
            shorten_links=input_data.shorten_links,
            unsplash=input_data.unsplash,
            requires_approval=input_data.requires_approval,
            random_post=input_data.random_post,
            random_media_url=input_data.random_media_url,
            notes=input_data.notes,
            bluesky_options=bluesky_options if bluesky_options else None,
            profile_key=profile_key.get_secret_value(),
        )
        yield "post_result", response
        if response.postIds:
            for p in response.postIds:
                yield "post", p