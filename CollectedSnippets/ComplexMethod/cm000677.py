def get_blocked_users(
        credentials: TwitterCredentials,
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

            response = cast(Response, client.get_blocked(**params))

            meta = {}
            user_ids = []
            usernames = []
            next_token = None

            included = IncludesSerializer.serialize(response.includes)

            if response.data:
                for user in response.data:
                    user_ids.append(str(user.id))
                    usernames.append(user.username)

            if response.meta:
                meta = response.meta
                if "next_token" in meta:
                    next_token = meta["next_token"]

            if user_ids and usernames:
                return included, meta, user_ids, usernames, next_token
            else:
                raise tweepy.TweepyException("No blocked users found")

        except tweepy.TweepyException:
            raise