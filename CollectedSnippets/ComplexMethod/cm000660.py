def get_liked_tweets(
        credentials: TwitterCredentials,
        user_id: str,
        max_results: int | None,
        pagination_token: str | None,
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
                "pagination_token": (
                    None if pagination_token == "" else pagination_token
                ),
                "user_auth": False,
            }

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

            response = cast(Response, client.get_liked_tweets(**params))

            if not response.data and not response.meta:
                raise Exception("No liked tweets found")

            meta = {}
            tweet_ids = []
            tweet_texts = []
            user_ids = []
            user_names = []
            next_token = None

            if response.meta:
                meta = response.meta
                next_token = meta.get("next_token")

            included = IncludesSerializer.serialize(response.includes)
            data = ResponseDataSerializer.serialize_list(response.data)

            if response.data:
                tweet_ids = [str(tweet.id) for tweet in response.data]
                tweet_texts = [tweet.text for tweet in response.data]

                if "users" in response.includes:
                    user_ids = [str(user["id"]) for user in response.includes["users"]]
                    user_names = [
                        user["username"] for user in response.includes["users"]
                    ]

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

            raise Exception("No liked tweets found")

        except tweepy.TweepyException:
            raise