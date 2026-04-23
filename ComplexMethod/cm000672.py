def post_tweet(
        self,
        credentials: TwitterCredentials,
        input_txt: str | None,
        attachment: Union[Media, DeepLink, Poll, Place, Quote] | None,
        for_super_followers_only: bool,
        exclude_reply_user_ids: Optional[List[str]],
        in_reply_to_tweet_id: Optional[str],
        reply_settings: TweetReplySettingsFilter,
    ):
        try:
            client = tweepy.Client(
                bearer_token=credentials.access_token.get_secret_value()
            )

            params = (
                TweetPostBuilder()
                .add_text(input_txt)
                .add_super_followers(for_super_followers_only)
                .add_reply_settings(
                    exclude_reply_user_ids or [],
                    in_reply_to_tweet_id or "",
                    reply_settings,
                )
            )

            if isinstance(attachment, Media):
                params.add_media(
                    attachment.media_ids or [], attachment.media_tagged_user_ids or []
                )
            elif isinstance(attachment, DeepLink):
                params.add_deep_link(attachment.direct_message_deep_link or "")
            elif isinstance(attachment, Poll):
                params.add_poll_options(attachment.poll_options or [])
                params.add_poll_duration(attachment.poll_duration_minutes or 0)
            elif isinstance(attachment, Place):
                params.add_place(attachment.place_id or "")
            elif isinstance(attachment, Quote):
                params.add_quote(attachment.quote_tweet_id or "")

            tweet = cast(Response, client.create_tweet(**params.build()))

            if not tweet.data:
                raise Exception("Failed to create tweet")

            tweet_id = tweet.data["id"]
            tweet_url = f"https://twitter.com/user/status/{tweet_id}"
            return str(tweet_id), tweet_url

        except tweepy.TweepyException:
            raise
        except Exception:
            raise