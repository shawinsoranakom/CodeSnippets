def get_tweets(
        credentials: TwitterCredentials,
        tweet_ids: list[str],
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
            params = {"ids": tweet_ids, "user_auth": False}

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

            response = cast(Response, client.get_tweets(**params))

            if not response.data and not response.meta:
                raise Exception("No tweets found")

            tweet_ids = []
            tweet_texts = []
            user_ids = []
            user_names = []
            meta = {}

            included = IncludesSerializer.serialize(response.includes)
            data = ResponseDataSerializer.serialize_list(response.data)

            if response.data:
                tweet_ids = [str(tweet.id) for tweet in response.data]
                tweet_texts = [tweet.text for tweet in response.data]

            if included and "users" in included:
                for user in included["users"]:
                    user_ids.append(str(user["id"]))
                    user_names.append(user["username"])

            if response.meta:
                meta = response.meta

            return tweet_ids, tweet_texts, user_ids, user_names, data, included, meta

        except tweepy.TweepyException:
            raise