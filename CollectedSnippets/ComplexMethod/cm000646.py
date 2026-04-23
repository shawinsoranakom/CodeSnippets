def get_spaces(
        credentials: TwitterCredentials,
        identifier: Union[SpaceList, UserList],
        expansions: SpaceExpansionsFilter | None,
        space_fields: SpaceFieldsFilter | None,
        user_fields: TweetUserFieldsFilter | None,
    ):
        try:
            client = tweepy.Client(
                bearer_token=credentials.access_token.get_secret_value()
            )

            params = {
                "ids": (
                    identifier.space_ids if isinstance(identifier, SpaceList) else None
                ),
                "user_ids": (
                    identifier.user_ids if isinstance(identifier, UserList) else None
                ),
            }

            params = (
                SpaceExpansionsBuilder(params)
                .add_expansions(expansions)
                .add_space_fields(space_fields)
                .add_user_fields(user_fields)
                .build()
            )

            response = cast(Response, client.get_spaces(**params))

            ids = []
            titles = []

            included = IncludesSerializer.serialize(response.includes)

            if response.data:
                data = ResponseDataSerializer.serialize_list(response.data)
                ids = [space["id"] for space in data if "id" in space]
                titles = [space["title"] for space in data if "title" in space]

                return data, included, ids, titles

            raise Exception("No spaces found")

        except tweepy.TweepyException:
            raise