def get_owned_lists(
        credentials: TwitterCredentials,
        user_id: str,
        max_results: int | None,
        pagination_token: str | None,
        expansions: ListExpansionsFilter | None,
        user_fields: TweetUserFieldsFilter | None,
        list_fields: ListFieldsFilter | None,
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
                ListExpansionsBuilder(params)
                .add_expansions(expansions)
                .add_user_fields(user_fields)
                .add_list_fields(list_fields)
                .build()
            )

            response = cast(Response, client.get_owned_lists(**params))

            meta = {}
            included = {}
            list_ids = []
            list_names = []
            next_token = None

            if response.meta:
                meta = response.meta
                next_token = meta.get("next_token")

            if response.includes:
                included = IncludesSerializer.serialize(response.includes)

            if response.data:
                data = ResponseDataSerializer.serialize_list(response.data)
                list_ids = [
                    str(item.id) for item in response.data if hasattr(item, "id")
                ]
                list_names = [
                    item.name for item in response.data if hasattr(item, "name")
                ]

                return data, included, meta, list_ids, list_names, next_token

            raise Exception("User have no owned list")

        except tweepy.TweepyException:
            raise