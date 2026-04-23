def get_list_memberships(
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

            response = cast(Response, client.get_list_memberships(**params))

            meta = {}
            included = {}
            next_token = None
            list_ids = []

            if response.meta:
                meta = response.meta
                next_token = meta.get("next_token")

            if response.includes:
                included = IncludesSerializer.serialize(response.includes)

            if response.data:
                data = ResponseDataSerializer.serialize_list(response.data)
                list_ids = [str(lst.id) for lst in response.data]
                return data, included, meta, list_ids, next_token

            raise Exception("List memberships not found")

        except tweepy.TweepyException:
            raise
        except Exception:
            raise