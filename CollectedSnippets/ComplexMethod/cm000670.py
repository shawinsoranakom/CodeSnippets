def get_user_tweets(
        credentials: TwitterCredentials,
        user_id: str,
        max_results: int | None,
        start_time: datetime | None,
        end_time: datetime | None,
        since_id: str | None,
        until_id: str | None,
        sort_order: str | None,
        pagination: str | None,
        expansions: ExpansionFilter | None,
        media_fields: TweetMediaFieldsFilter | None,
        place_fields: TweetPlaceFieldsFilter | None,
        poll_fields: TweetPollFieldsFilter | None,
        tweet_fields: TweetFieldsFilter | None,
        user_fields: TweetUserFieldsFilter | None,
    ):
        try:
            client = tweepy.Client(
                bearer_token=credentials.access_token.get_secret_value()
            )

            params = {
                "id": user_id,
                "max_results": max_results,
                "pagination_token": None if pagination == "" else pagination,
                "user_auth": False,
            }

            # Adding expansions to params If required by the user
            params = (
                TweetExpansionsBuilder(params)
                .add_expansions(expansions)
                .add_media_fields(media_fields)
                .add_place_fields(place_fields)
                .add_poll_fields(poll_fields)
                .add_tweet_fields(tweet_fields)
                .add_user_fields(user_fields)
                .build()
            )

            # Adding time window to params If required by the user
            params = (
                TweetDurationBuilder(params)
                .add_start_time(start_time)
                .add_end_time(end_time)
                .add_since_id(since_id)
                .add_until_id(until_id)
                .add_sort_order(sort_order)
                .build()
            )

            response = cast(
                Response,
                client.get_users_tweets(**params),
            )

            if not response.data and not response.meta:
                raise Exception("No tweets found")

            included = IncludesSerializer.serialize(response.includes)
            data = ResponseDataSerializer.serialize_list(response.data)
            meta = response.meta or {}
            next_token = meta.get("next_token", "")

            tweet_ids = []
            tweet_texts = []
            user_ids = []
            user_names = []

            if response.data:
                tweet_ids = [str(tweet.id) for tweet in response.data]
                tweet_texts = [tweet.text for tweet in response.data]

            if "users" in included:
                user_ids = [str(user["id"]) for user in included["users"]]
                user_names = [user["username"] for user in included["users"]]

            return (
                tweet_ids,
                tweet_texts,
                user_ids,
                user_names,
                data,
                included,
                meta,
                next_token,
            )

        except tweepy.TweepyException:
            raise