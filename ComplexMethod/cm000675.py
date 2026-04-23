def get_quote_tweets(
        credentials: TwitterCredentials,
        tweet_id: str,
        max_results: int | None,
        exclude: TweetExcludesFilter | None,
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
                "id": tweet_id,
                "max_results": max_results,
                "pagination_token": (
                    None if pagination_token == "" else pagination_token
                ),
                "exclude": None if exclude == TweetExcludesFilter() else exclude,
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

            response = cast(Response, client.get_quote_tweets(**params))

            meta = {}
            tweet_ids = []
            tweet_texts = []
            next_token = None

            if response.meta:
                meta = response.meta
                next_token = meta.get("next_token")

            included = IncludesSerializer.serialize(response.includes)
            data = ResponseDataSerializer.serialize_list(response.data)

            if response.data:
                tweet_ids = [str(tweet.id) for tweet in response.data]
                tweet_texts = [tweet.text for tweet in response.data]

                return tweet_ids, tweet_texts, data, included, meta, next_token

            raise Exception("No quote tweets found")

        except tweepy.TweepyException:
            raise