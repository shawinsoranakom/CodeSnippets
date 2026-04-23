async def run(
        self,
        input_data: "PostToInstagramBlock.Input",
        *,
        user_id: str,
        **kwargs,
    ) -> BlockOutput:
        """Post to Instagram with Instagram-specific options."""
        profile_key = await get_profile_key(user_id)
        if not profile_key:
            yield "error", "Please link a social account via Ayrshare"
            return

        client = create_ayrshare_client()
        if not client:
            yield "error", "Ayrshare integration is not configured. Please set up the AYRSHARE_API_KEY."
            return

        # Validate Instagram constraints
        if len(input_data.post) > 2200:
            yield "error", f"Instagram post text exceeds 2,200 character limit ({len(input_data.post)} characters)"
            return

        if len(input_data.media_urls) > 10:
            yield "error", "Instagram supports a maximum of 10 images/videos in a carousel"
            return

        if len(input_data.collaborators) > 3:
            yield "error", "Instagram supports a maximum of 3 collaborators"
            return

        # Validate that if any reel option is set, all required reel options are set
        reel_options = [
            input_data.share_reels_feed,
            input_data.audio_name,
            input_data.thumbnail,
        ]

        if any(reel_options) and not all(reel_options):
            yield "error", "When posting a reel, all reel options must be set: share_reels_feed, audio_name, and either thumbnail or thumbnail_offset"
            return

        # Count hashtags and mentions
        hashtag_count = input_data.post.count("#")
        mention_count = input_data.post.count("@")

        if hashtag_count > 30:
            yield "error", f"Instagram allows maximum 30 hashtags ({hashtag_count} found)"
            return

        if mention_count > 3:
            yield "error", f"Instagram allows maximum 3 @mentions ({mention_count} found)"
            return

        # Convert datetime to ISO format if provided
        iso_date = (
            input_data.schedule_date.isoformat() if input_data.schedule_date else None
        )

        # Build Instagram-specific options
        instagram_options = {}

        # Stories
        if input_data.is_story:
            instagram_options["stories"] = True

        # Reels options
        if input_data.share_reels_feed is not None:
            instagram_options["shareReelsFeed"] = input_data.share_reels_feed

        if input_data.audio_name:
            instagram_options["audioName"] = input_data.audio_name

        if input_data.thumbnail:
            instagram_options["thumbNail"] = input_data.thumbnail
        elif input_data.thumbnail_offset and input_data.thumbnail_offset > 0:
            instagram_options["thumbNailOffset"] = input_data.thumbnail_offset

        # Alt text
        if input_data.alt_text:
            # Validate alt text length
            for i, alt in enumerate(input_data.alt_text):
                if len(alt) > 1000:
                    yield "error", f"Alt text {i+1} exceeds 1,000 character limit ({len(alt)} characters)"
                    return
            instagram_options["altText"] = input_data.alt_text

        # Location
        if input_data.location_id:
            instagram_options["locationId"] = input_data.location_id

        # User tags
        if input_data.user_tags:
            user_tags_list = []
            for tag in input_data.user_tags:
                try:
                    tag_obj = InstagramUserTag(**tag)
                except Exception as e:
                    yield "error", f"Invalid user tag: {e}, tages need to be a dictionary with a 3 items: username (str), x (float) and y (float)"
                    return
                tag_dict: dict[str, float | str] = {"username": tag_obj.username}
                if tag_obj.x is not None and tag_obj.y is not None:
                    # Validate coordinates
                    if not (0.0 <= tag_obj.x <= 1.0) or not (0.0 <= tag_obj.y <= 1.0):
                        yield "error", f"User tag coordinates must be between 0.0 and 1.0 (user: {tag_obj.username})"
                        return
                    tag_dict["x"] = tag_obj.x
                    tag_dict["y"] = tag_obj.y
                user_tags_list.append(tag_dict)
            instagram_options["userTags"] = user_tags_list

        # Collaborators
        if input_data.collaborators:
            instagram_options["collaborators"] = input_data.collaborators

        # Auto resize
        if input_data.auto_resize:
            instagram_options["autoResize"] = True

        response = await client.create_post(
            post=input_data.post,
            platforms=[SocialPlatform.INSTAGRAM],
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
            instagram_options=instagram_options if instagram_options else None,
            profile_key=profile_key.get_secret_value(),
        )
        yield "post_result", response
        if response.postIds:
            for p in response.postIds:
                yield "post", p