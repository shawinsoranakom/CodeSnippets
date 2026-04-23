async def run(
        self,
        input_data: "PostToFacebookBlock.Input",
        *,
        user_id: str,
        **kwargs,
    ) -> BlockOutput:
        """Post to Facebook with Facebook-specific options."""
        profile_key = await get_profile_key(user_id)
        if not profile_key:
            yield "error", "Please link a social account via Ayrshare"
            return

        client = create_ayrshare_client()
        if not client:
            yield "error", "Ayrshare integration is not configured. Please set up the AYRSHARE_API_KEY."
            return

        # Convert datetime to ISO format if provided
        iso_date = (
            input_data.schedule_date.isoformat() if input_data.schedule_date else None
        )

        # Build Facebook-specific options
        facebook_options = {}
        if input_data.is_carousel:
            facebook_options["isCarousel"] = True
            if input_data.carousel_link:
                facebook_options["carouselLink"] = input_data.carousel_link
            if input_data.carousel_items:
                facebook_options["carouselItems"] = [
                    item.dict() for item in input_data.carousel_items
                ]

        if input_data.is_reels:
            facebook_options["isReels"] = True
            if input_data.reels_title:
                facebook_options["reelsTitle"] = input_data.reels_title
            if input_data.reels_thumbnail:
                facebook_options["reelsThumbnail"] = input_data.reels_thumbnail

        if input_data.is_story:
            facebook_options["isStory"] = True

        if input_data.media_captions:
            facebook_options["mediaCaptions"] = input_data.media_captions

        if input_data.location_id:
            facebook_options["locationId"] = input_data.location_id

        if input_data.age_min > 0:
            facebook_options["ageMin"] = input_data.age_min

        if input_data.target_countries:
            facebook_options["targetCountries"] = input_data.target_countries

        if input_data.alt_text:
            facebook_options["altText"] = input_data.alt_text

        if input_data.video_title:
            facebook_options["videoTitle"] = input_data.video_title

        if input_data.video_thumbnail:
            facebook_options["videoThumbnail"] = input_data.video_thumbnail

        if input_data.is_draft:
            facebook_options["isDraft"] = True

        if input_data.scheduled_publish_date:
            facebook_options["scheduledPublishDate"] = input_data.scheduled_publish_date

        if input_data.preview_link:
            facebook_options["previewLink"] = input_data.preview_link

        response = await client.create_post(
            post=input_data.post,
            platforms=[SocialPlatform.FACEBOOK],
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
            facebook_options=facebook_options if facebook_options else None,
            profile_key=profile_key.get_secret_value(),
        )
        yield "post_result", response
        if response.postIds:
            for p in response.postIds:
                yield "post", p