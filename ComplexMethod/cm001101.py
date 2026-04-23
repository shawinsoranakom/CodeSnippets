async def create_post(
        self,
        post: str,
        platforms: list[SocialPlatform],
        *,
        media_urls: Optional[list[str]] = None,
        is_video: Optional[bool] = None,
        schedule_date: Optional[str] = None,
        validate_schedule: Optional[bool] = None,
        first_comment: Optional[FirstComment] = None,
        disable_comments: Optional[bool] = None,
        shorten_links: Optional[bool] = None,
        auto_schedule: Optional[AutoSchedule] = None,
        auto_repost: Optional[AutoRepost] = None,
        auto_hashtag: Optional[AutoHashtag | bool] = None,
        unsplash: Optional[str] = None,
        bluesky_options: Optional[dict[str, Any]] = None,
        facebook_options: Optional[dict[str, Any]] = None,
        gmb_options: Optional[dict[str, Any]] = None,
        instagram_options: Optional[dict[str, Any]] = None,
        linkedin_options: Optional[dict[str, Any]] = None,
        pinterest_options: Optional[dict[str, Any]] = None,
        reddit_options: Optional[dict[str, Any]] = None,
        snapchat_options: Optional[dict[str, Any]] = None,
        telegram_options: Optional[dict[str, Any]] = None,
        threads_options: Optional[dict[str, Any]] = None,
        tiktok_options: Optional[dict[str, Any]] = None,
        twitter_options: Optional[dict[str, Any]] = None,
        youtube_options: Optional[dict[str, Any]] = None,
        requires_approval: Optional[bool] = None,
        random_post: Optional[bool] = None,
        random_media_url: Optional[bool] = None,
        idempotency_key: Optional[str] = None,
        notes: Optional[str] = None,
        profile_key: Optional[str] = None,
    ) -> PostResponse:
        """
        Create a post across multiple social media platforms.

        Docs: https://www.ayrshare.com/docs/apis/post/post

        Args:
            post: The post text to be published - required
            platforms: List of platforms to post to (e.g. [SocialPlatform.TWITTER, SocialPlatform.FACEBOOK]) - required
            media_urls: Optional list of media URLs to include - required if is_video is true
            is_video: Whether the media is a video - default is false (in api docs)
            schedule_date: UTC datetime for scheduling (YYYY-MM-DDThh:mm:ssZ) - default is None (in api docs)
            validate_schedule: Whether to validate the schedule date - default is false (in api docs)
            first_comment: Configuration for first comment - default is None (in api docs)
            disable_comments: Whether to disable comments - default is false (in api docs)
            shorten_links: Whether to shorten links - default is false (in api docs)
            auto_schedule: Configuration for automatic scheduling - default is None (in api docs https://www.ayrshare.com/docs/apis/auto-schedule/overview)
            auto_repost: Configuration for automatic reposting - default is None (in api docs https://www.ayrshare.com/docs/apis/post/overview#auto-repost)
            auto_hashtag: Configuration for automatic hashtags - default is None (in api docs https://www.ayrshare.com/docs/apis/post/overview#auto-hashtags)
            unsplash: Unsplash image configuration - default is None (in api docs https://www.ayrshare.com/docs/apis/post/overview#unsplash)

            ------------------------------------------------------------

            bluesky_options: Bluesky-specific options - https://www.ayrshare.com/docs/apis/post/social-networks/bluesky
            facebook_options: Facebook-specific options - https://www.ayrshare.com/docs/apis/post/social-networks/facebook
            gmb_options: Google Business Profile options - https://www.ayrshare.com/docs/apis/post/social-networks/google
            instagram_options: Instagram-specific options - https://www.ayrshare.com/docs/apis/post/social-networks/instagram
            linkedin_options: LinkedIn-specific options - https://www.ayrshare.com/docs/apis/post/social-networks/linkedin
            pinterest_options: Pinterest-specific options - https://www.ayrshare.com/docs/apis/post/social-networks/pinterest
            reddit_options: Reddit-specific options - https://www.ayrshare.com/docs/apis/post/social-networks/reddit
            snapchat_options: Snapchat-specific options - https://www.ayrshare.com/docs/apis/post/social-networks/snapchat
            telegram_options: Telegram-specific options - https://www.ayrshare.com/docs/apis/post/social-networks/telegram
            threads_options: Threads-specific options - https://www.ayrshare.com/docs/apis/post/social-networks/threads
            tiktok_options: TikTok-specific options - https://www.ayrshare.com/docs/apis/post/social-networks/tiktok
            twitter_options: Twitter-specific options - https://www.ayrshare.com/docs/apis/post/social-networks/twitter
            youtube_options: YouTube-specific options - https://www.ayrshare.com/docs/apis/post/social-networks/youtube

            ------------------------------------------------------------


            requires_approval: Whether to enable approval workflow - default is false (in api docs)
            random_post: Whether to generate random post text - default is false (in api docs)
            random_media_url: Whether to generate random media - default is false (in api docs)
            idempotency_key: Unique ID for the post - default is None (in api docs)
            notes: Additional notes for the post - default is None (in api docs)

        Returns:
            PostResponse object containing the post details and status

        Raises:
            AyrshareAPIException: If the API request fails
        """

        payload: dict[str, Any] = {
            "post": post,
            "platforms": [p.value for p in platforms],
        }

        # Add optional parameters if provided
        if media_urls:
            payload["mediaUrls"] = media_urls
        if is_video is not None:
            payload["isVideo"] = is_video
        if schedule_date:
            payload["scheduleDate"] = schedule_date
        if validate_schedule is not None:
            payload["validateSchedule"] = validate_schedule
        if first_comment:
            first_comment_dict = first_comment.model_dump(exclude_none=True)
            if first_comment.platforms:
                first_comment_dict["platforms"] = [
                    p.value for p in first_comment.platforms
                ]
            payload["firstComment"] = first_comment_dict
        if disable_comments is not None:
            payload["disableComments"] = disable_comments
        if shorten_links is not None:
            payload["shortenLinks"] = shorten_links
        if auto_schedule:
            auto_schedule_dict = auto_schedule.model_dump(exclude_none=True)
            if auto_schedule.platforms:
                auto_schedule_dict["platforms"] = [
                    p.value for p in auto_schedule.platforms
                ]
            payload["autoSchedule"] = auto_schedule_dict
        if auto_repost:
            auto_repost_dict = auto_repost.model_dump(exclude_none=True)
            if auto_repost.platforms:
                auto_repost_dict["platforms"] = [p.value for p in auto_repost.platforms]
            payload["autoRepost"] = auto_repost_dict
        if auto_hashtag:
            payload["autoHashtag"] = (
                auto_hashtag.model_dump(exclude_none=True)
                if isinstance(auto_hashtag, AutoHashtag)
                else auto_hashtag
            )
        if unsplash:
            payload["unsplash"] = unsplash
        if bluesky_options:
            payload["blueskyOptions"] = bluesky_options
        if facebook_options:
            payload["faceBookOptions"] = facebook_options
        if gmb_options:
            payload["gmbOptions"] = gmb_options
        if instagram_options:
            payload["instagramOptions"] = instagram_options
        if linkedin_options:
            payload["linkedInOptions"] = linkedin_options
        if pinterest_options:
            payload["pinterestOptions"] = pinterest_options
        if reddit_options:
            payload["redditOptions"] = reddit_options
        if snapchat_options:
            payload["snapchatOptions"] = snapchat_options
        if telegram_options:
            payload["telegramOptions"] = telegram_options
        if threads_options:
            payload["threadsOptions"] = threads_options
        if tiktok_options:
            payload["tikTokOptions"] = tiktok_options
        if twitter_options:
            payload["twitterOptions"] = twitter_options
        if youtube_options:
            payload["youTubeOptions"] = youtube_options
        if requires_approval is not None:
            payload["requiresApproval"] = requires_approval
        if random_post is not None:
            payload["randomPost"] = random_post
        if random_media_url is not None:
            payload["randomMediaUrl"] = random_media_url
        if idempotency_key:
            payload["idempotencyKey"] = idempotency_key
        if notes:
            payload["notes"] = notes

        headers = self.headers
        if profile_key:
            headers["Profile-Key"] = profile_key

        response = await self._requests.post(
            self.POST_ENDPOINT, json=payload, headers=headers
        )
        logger.warning(f"Ayrshare request: {payload} and headers: {headers}")
        if not response.ok:
            logger.error(
                f"Ayrshare API request failed ({response.status}): {response.text()}"
            )
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
            logger.error(
                f"Ayrshare API returned error: {response_data.get('message', 'Unknown error')}"
            )
            raise AyrshareAPIException(
                f"Ayrshare API returned error: {response_data.get('message', 'Unknown error')}",
                response.status,
            )

        # Ayrshare returns an array of posts even for single posts
        # It seems like there is only ever one post in the array, and within that
        # there are multiple postIds

        # There is a seperate endpoint for bulk posting, so feels safe to just take
        # the first post from the array

        if len(response_data["posts"]) == 0:
            logger.error("Ayrshare API returned no posts")
            raise AyrshareAPIException(
                "Ayrshare API returned no posts",
                response.status,
            )
        logger.warn(f"Ayrshare API returned posts: {response_data['posts']}")
        return PostResponse(**response_data["posts"][0])