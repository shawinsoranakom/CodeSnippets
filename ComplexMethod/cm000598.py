async def run(
        self,
        input_data: "PostToThreadsBlock.Input",
        *,
        user_id: str,
        **kwargs,
    ) -> BlockOutput:
        """Post to Threads with Threads-specific validation."""
        profile_key = await get_profile_key(user_id)
        if not profile_key:
            yield "error", "Please link a social account via Ayrshare"
            return

        client = create_ayrshare_client()
        if not client:
            yield "error", "Ayrshare integration is not configured. Please set up the AYRSHARE_API_KEY."
            return

        # Validate Threads constraints
        if len(input_data.post) > 500:
            yield "error", f"Threads post text exceeds 500 character limit ({len(input_data.post)} characters)"
            return

        if len(input_data.media_urls) > 20:
            yield "error", "Threads supports a maximum of 20 images/videos in a carousel"
            return

        # Count hashtags (only 1 allowed)
        hashtag_count = input_data.post.count("#")
        if hashtag_count > 1:
            yield "error", f"Threads allows only 1 hashtag per post ({hashtag_count} found)"
            return

        # Convert datetime to ISO format if provided
        iso_date = (
            input_data.schedule_date.isoformat() if input_data.schedule_date else None
        )

        # Build Threads-specific options
        threads_options = {}
        # Note: Based on the documentation, Threads doesn't seem to have specific options
        # beyond the standard ones. The main constraints are validation-based.

        response = await client.create_post(
            post=input_data.post,
            platforms=[SocialPlatform.THREADS],
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
            threads_options=threads_options if threads_options else None,
            profile_key=profile_key.get_secret_value(),
        )
        yield "post_result", response
        if response.postIds:
            for p in response.postIds:
                yield "post", p