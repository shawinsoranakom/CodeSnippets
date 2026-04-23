def get_liking_users(
        credentials: TwitterCredentials,
        tweet_id: str,
        max_results: int | None,
        pagination_token: str | None,
        expansions: UserExpansionsFilter | None,
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
                "user_auth": False,
            }

            params = (
                UserExpansionsBuilder(params)
                .add_expansions(expansions)
                .add_tweet_fields(tweet_fields)
                .add_user_fields(user_fields)
                .build()
            )

            response = cast(Response, client.get_liking_users(**params))

            if not response.data and not response.meta:
                raise Exception("No liking users found")

            meta = {}
            user_ids = []
            usernames = []
            next_token = None

            if response.meta:
                meta = response.meta
                next_token = meta.get("next_token")

            included = IncludesSerializer.serialize(response.includes)
            data = ResponseDataSerializer.serialize_list(response.data)

            if response.data:
                user_ids = [str(user.id) for user in response.data]
                usernames = [user.username for user in response.data]

                return user_ids, usernames, data, included, meta, next_token

            raise Exception("No liking users found")

        except tweepy.TweepyException:
            raise