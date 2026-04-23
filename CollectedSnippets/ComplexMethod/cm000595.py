async def run(
        self, input_data: "PostToGMBBlock.Input", *, user_id: str, **kwargs
    ) -> BlockOutput:
        """Post to Google My Business with GMB-specific options."""
        profile_key = await get_profile_key(user_id)
        if not profile_key:
            yield "error", "Please link a social account via Ayrshare"
            return

        client = create_ayrshare_client()
        if not client:
            yield "error", "Ayrshare integration is not configured. Please set up the AYRSHARE_API_KEY."
            return

        # Validate GMB constraints
        if len(input_data.media_urls) > 1:
            yield "error", "Google My Business supports only one image or video per post"
            return

        # Validate offer coupon code length
        if input_data.offer_coupon_code and len(input_data.offer_coupon_code) > 58:
            yield "error", "GMB offer coupon code cannot exceed 58 characters"
            return

        # Convert datetime to ISO format if provided
        iso_date = (
            input_data.schedule_date.isoformat() if input_data.schedule_date else None
        )

        # Build GMB-specific options
        gmb_options = {}

        # Photo/Video post options
        if input_data.is_photo_video:
            gmb_options["isPhotoVideo"] = True
            if input_data.photo_category:
                gmb_options["category"] = input_data.photo_category

        # Call to Action (from flattened fields)
        if input_data.call_to_action_type:
            cta_dict = {"actionType": input_data.call_to_action_type}
            # URL not required for 'call' action type
            if (
                input_data.call_to_action_type != "call"
                and input_data.call_to_action_url
            ):
                cta_dict["url"] = input_data.call_to_action_url
            gmb_options["callToAction"] = cta_dict

        # Event details (from flattened fields)
        if (
            input_data.event_title
            and input_data.event_start_date
            and input_data.event_end_date
        ):
            gmb_options["event"] = {
                "title": input_data.event_title,
                "startDate": input_data.event_start_date,
                "endDate": input_data.event_end_date,
            }

        # Offer details (from flattened fields)
        if (
            input_data.offer_title
            and input_data.offer_start_date
            and input_data.offer_end_date
            and input_data.offer_coupon_code
            and input_data.offer_redeem_online_url
            and input_data.offer_terms_conditions
        ):
            gmb_options["offer"] = {
                "title": input_data.offer_title,
                "startDate": input_data.offer_start_date,
                "endDate": input_data.offer_end_date,
                "couponCode": input_data.offer_coupon_code,
                "redeemOnlineUrl": input_data.offer_redeem_online_url,
                "termsConditions": input_data.offer_terms_conditions,
            }

        response = await client.create_post(
            post=input_data.post,
            platforms=[SocialPlatform.GOOGLE_MY_BUSINESS],
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
            gmb_options=gmb_options if gmb_options else None,
            profile_key=profile_key.get_secret_value(),
        )
        yield "post_result", response
        if response.postIds:
            for p in response.postIds:
                yield "post", p