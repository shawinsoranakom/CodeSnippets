def get_space(
        credentials: TwitterCredentials,
        space_id: str,
        expansions: SpaceExpansionsFilter | None,
        space_fields: SpaceFieldsFilter | None,
        user_fields: TweetUserFieldsFilter | None,
    ):
        try:
            client = tweepy.Client(
                bearer_token=credentials.access_token.get_secret_value()
            )

            params = {
                "id": space_id,
            }

            params = (
                SpaceExpansionsBuilder(params)
                .add_expansions(expansions)
                .add_space_fields(space_fields)
                .add_user_fields(user_fields)
                .build()
            )

            response = cast(Response, client.get_space(**params))

            includes = {}
            if response.includes:
                for key, value in response.includes.items():
                    if isinstance(value, list):
                        includes[key] = [
                            item.data if hasattr(item, "data") else item
                            for item in value
                        ]
                    else:
                        includes[key] = value.data if hasattr(value, "data") else value

            data = {}
            if response.data:
                for key, value in response.data.items():
                    if isinstance(value, list):
                        data[key] = [
                            item.data if hasattr(item, "data") else item
                            for item in value
                        ]
                    else:
                        data[key] = value.data if hasattr(value, "data") else value

                return data, includes

            raise Exception("Space not found")

        except tweepy.TweepyException:
            raise