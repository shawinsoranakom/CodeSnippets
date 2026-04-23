def get_list_tweets(
        credentials: TwitterCredentials,
        list_id: str,
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
                "id": list_id,
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

            response = cast(Response, client.get_list_tweets(**params))

            meta = {}
            included = {}
            tweet_ids = []
            texts = []
            next_token = None

            if response.meta:
                meta = response.meta
                next_token = meta.get("next_token")

            if response.includes:
                included = IncludesSerializer.serialize(response.includes)

            if response.data:
                data = ResponseDataSerializer.serialize_list(response.data)
                tweet_ids = [str(item.id) for item in response.data]
                texts = [item.text for item in response.data]

                return data, included, meta, tweet_ids, texts, next_token

            raise Exception("No tweets found in this list")

        except tweepy.TweepyException:
            raise