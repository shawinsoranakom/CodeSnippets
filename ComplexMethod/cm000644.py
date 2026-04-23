def search_spaces(
        credentials: TwitterCredentials,
        query: str,
        max_results: int | None,
        state: SpaceStatesFilter,
        expansions: SpaceExpansionsFilter | None,
        space_fields: SpaceFieldsFilter | None,
        user_fields: TweetUserFieldsFilter | None,
    ):
        try:
            client = tweepy.Client(
                bearer_token=credentials.access_token.get_secret_value()
            )

            params = {"query": query, "max_results": max_results, "state": state.value}

            params = (
                SpaceExpansionsBuilder(params)
                .add_expansions(expansions)
                .add_space_fields(space_fields)
                .add_user_fields(user_fields)
                .build()
            )

            response = cast(Response, client.search_spaces(**params))

            meta = {}
            next_token = ""
            if response.meta:
                meta = response.meta
                if "next_token" in meta:
                    next_token = meta["next_token"]

            included = IncludesSerializer.serialize(response.includes)
            data = ResponseDataSerializer.serialize_list(response.data)

            if response.data:
                ids = [str(space["id"]) for space in response.data if "id" in space]
                titles = [space["title"] for space in data if "title" in space]
                host_ids = [space["host_ids"] for space in data if "host_ids" in space]

                return data, included, meta, ids, titles, host_ids, next_token

            raise Exception("Spaces not found")

        except tweepy.TweepyException:
            raise