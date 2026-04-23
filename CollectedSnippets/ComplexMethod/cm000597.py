async def run(
        self,
        input_data: "PostToYouTubeBlock.Input",
        *,
        user_id: str,
        **kwargs,
    ) -> BlockOutput:
        """Post to YouTube with YouTube-specific validation and options."""

        profile_key = await get_profile_key(user_id)
        if not profile_key:
            yield "error", "Please link a social account via Ayrshare"
            return

        client = create_ayrshare_client()
        if not client:
            yield "error", "Ayrshare integration is not configured. Please set up the AYRSHARE_API_KEY."
            return

        # Validate YouTube constraints
        if not input_data.title:
            yield "error", "YouTube requires a video title"
            return

        if len(input_data.title) > 100:
            yield "error", f"YouTube title exceeds 100 character limit ({len(input_data.title)} characters)"
            return

        if len(input_data.post) > 5000:
            yield "error", f"YouTube description exceeds 5,000 character limit ({len(input_data.post)} characters)"
            return

        # Check for forbidden characters
        forbidden_chars = ["<", ">"]
        for char in forbidden_chars:
            if char in input_data.title:
                yield "error", f"YouTube title cannot contain '{char}' character"
                return
            if char in input_data.post:
                yield "error", f"YouTube description cannot contain '{char}' character"
                return

        if not input_data.media_urls:
            yield "error", "YouTube requires exactly one video URL"
            return

        if len(input_data.media_urls) > 1:
            yield "error", "YouTube supports only 1 video per post"
            return

        # Validate visibility option
        valid_visibility = ["private", "public", "unlisted"]
        if input_data.visibility not in valid_visibility:
            yield "error", f"YouTube visibility must be one of: {', '.join(valid_visibility)}"
            return

        # Validate thumbnail URL format
        if input_data.thumbnail:
            valid_extensions = [".png", ".jpg", ".jpeg"]
            if not any(
                input_data.thumbnail.lower().endswith(ext) for ext in valid_extensions
            ):
                yield "error", "YouTube thumbnail must end in .png, .jpg, or .jpeg"
                return

        # Validate tags
        if input_data.tags:
            total_tag_length = sum(len(tag) for tag in input_data.tags)
            if total_tag_length > 500:
                yield "error", f"YouTube tags total length exceeds 500 characters ({total_tag_length} characters)"
                return

            for tag in input_data.tags:
                if len(tag) < 2:
                    yield "error", f"YouTube tag '{tag}' is too short (minimum 2 characters)"
                    return

        # Validate subtitle URL
        if input_data.subtitle_url:
            if not input_data.subtitle_url.startswith("https://"):
                yield "error", "YouTube subtitle URL must start with https://"
                return

            valid_subtitle_extensions = [".srt", ".sbv"]
            if not any(
                input_data.subtitle_url.lower().endswith(ext)
                for ext in valid_subtitle_extensions
            ):
                yield "error", "YouTube subtitle URL must end in .srt or .sbv"
                return

        if input_data.subtitle_name and len(input_data.subtitle_name) > 150:
            yield "error", f"YouTube subtitle name exceeds 150 character limit ({len(input_data.subtitle_name)} characters)"
            return

        # Validate publish_at format if provided
        if input_data.publish_at and input_data.schedule_date:
            yield "error", "Cannot use both 'publish_at' and 'schedule_date'. Use 'publish_at' for YouTube-controlled publishing."
            return

        # Convert datetime to ISO format if provided (only if not using publish_at)
        iso_date = None
        if not input_data.publish_at and input_data.schedule_date:
            iso_date = input_data.schedule_date.isoformat()

        # Build YouTube-specific options
        youtube_options: dict[str, Any] = {"title": input_data.title}

        # Basic options
        if input_data.visibility != "private":
            youtube_options["visibility"] = input_data.visibility

        if input_data.thumbnail:
            youtube_options["thumbNail"] = input_data.thumbnail

        if input_data.playlist_id:
            youtube_options["playListId"] = input_data.playlist_id

        if input_data.tags:
            youtube_options["tags"] = input_data.tags

        if input_data.made_for_kids:
            youtube_options["madeForKids"] = True

        if input_data.is_shorts:
            youtube_options["shorts"] = True

        if not input_data.notify_subscribers:
            youtube_options["notifySubscribers"] = False

        if input_data.category_id and input_data.category_id > 0:
            youtube_options["categoryId"] = input_data.category_id

        if input_data.contains_synthetic_media:
            youtube_options["containsSyntheticMedia"] = True

        if input_data.publish_at:
            youtube_options["publishAt"] = input_data.publish_at

        # Country targeting (from flattened fields)
        targeting_dict = {}
        if input_data.targeting_block_countries:
            targeting_dict["block"] = input_data.targeting_block_countries
        if input_data.targeting_allow_countries:
            targeting_dict["allow"] = input_data.targeting_allow_countries

        if targeting_dict:
            youtube_options["targeting"] = targeting_dict

        # Subtitle options
        if input_data.subtitle_url:
            youtube_options["subTitleUrl"] = input_data.subtitle_url
            youtube_options["subTitleLanguage"] = input_data.subtitle_language
            youtube_options["subTitleName"] = input_data.subtitle_name

        response = await client.create_post(
            post=input_data.post,
            platforms=[SocialPlatform.YOUTUBE],
            media_urls=input_data.media_urls,
            is_video=True,  # YouTube only supports videos
            schedule_date=iso_date,
            disable_comments=input_data.disable_comments,
            shorten_links=input_data.shorten_links,
            unsplash=input_data.unsplash,
            requires_approval=input_data.requires_approval,
            random_post=input_data.random_post,
            random_media_url=input_data.random_media_url,
            notes=input_data.notes,
            youtube_options=youtube_options,
            profile_key=profile_key.get_secret_value(),
        )
        yield "post_result", response
        if response.postIds:
            for p in response.postIds:
                yield "post", p