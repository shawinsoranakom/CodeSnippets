def get_users(
        credentials: TwitterCredentials,
        identifier: Union[UserIdList, UsernameList],
        expansions: UserExpansionsFilter | None,
        tweet_fields: TweetFieldsFilter | None,
        user_fields: TweetUserFieldsFilter | None,
    ):
        try:
            client = tweepy.Client(
                bearer_token=credentials.access_token.get_secret_value()
            )

            params = {
                "ids": (
                    ",".join(identifier.user_ids)
                    if isinstance(identifier, UserIdList)
                    else None
                ),
                "usernames": (
                    ",".join(identifier.usernames)
                    if isinstance(identifier, UsernameList)
                    else None
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

            response = cast(Response, client.get_users(**params))

            usernames = []
            ids = []
            names = []

            included = IncludesSerializer.serialize(response.includes)
            data = ResponseDataSerializer.serialize_list(response.data)

            if response.data:
                for user in response.data:
                    usernames.append(user.username)
                    ids.append(str(user.id))
                    names.append(user.name)

            if usernames and ids:
                return data, included, usernames, ids, names
            else:
                raise tweepy.TweepyException("Users not found")

        except tweepy.TweepyException:
            raise