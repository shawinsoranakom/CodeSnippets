async def run(
        self,
        input_data: "PostToTelegramBlock.Input",
        *,
        user_id: str,
        **kwargs,
    ) -> BlockOutput:
        """Post to Telegram with Telegram-specific validation."""
        profile_key = await get_profile_key(user_id)
        if not profile_key:
            yield "error", "Please link a social account via Ayrshare"
            return

        client = create_ayrshare_client()
        if not client:
            yield "error", "Ayrshare integration is not configured. Please set up the AYRSHARE_API_KEY."
            return

        # Validate Telegram constraints
        # Check for animated GIFs - only one URL allowed
        gif_extensions = [".gif", ".GIF"]
        has_gif = any(
            any(url.endswith(ext) for ext in gif_extensions)
            for url in input_data.media_urls
        )

        if has_gif and len(input_data.media_urls) > 1:
            yield "error", "Telegram animated GIFs support only one URL per post"
            return

        # Auto-detect if we need to set is_video for GIFs without proper extension
        detected_is_video = input_data.is_video
        if input_data.media_urls and not has_gif and not input_data.is_video:
            # Check if this might be a GIF without proper extension
            # This is just informational - user needs to set is_video manually
            pass

        # Convert datetime to ISO format if provided
        iso_date = (
            input_data.schedule_date.isoformat() if input_data.schedule_date else None
        )

        response = await client.create_post(
            post=input_data.post,
            platforms=[SocialPlatform.TELEGRAM],
            media_urls=input_data.media_urls,
            is_video=detected_is_video,
            schedule_date=iso_date,
            disable_comments=input_data.disable_comments,
            shorten_links=input_data.shorten_links,
            unsplash=input_data.unsplash,
            requires_approval=input_data.requires_approval,
            random_post=input_data.random_post,
            random_media_url=input_data.random_media_url,
            notes=input_data.notes,
            profile_key=profile_key.get_secret_value(),
        )
        yield "post_result", response
        if response.postIds:
            for p in response.postIds:
                yield "post", p