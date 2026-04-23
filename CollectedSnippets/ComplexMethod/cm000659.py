async def run(
        self,
        input_data: Input,
        *,
        credentials: TwitterCredentials,
        **kwargs,
    ) -> BlockOutput:
        try:
            ids, usernames, data, included, meta, next_token = self.get_liking_users(
                credentials,
                input_data.tweet_id,
                input_data.max_results,
                input_data.pagination_token,
                input_data.expansions,
                input_data.tweet_fields,
                input_data.user_fields,
            )
            if ids:
                yield "id", ids
            if usernames:
                yield "username", usernames
            if next_token:
                yield "next_token", next_token
            if data:
                yield "data", data
            if included:
                yield "included", included
            if meta:
                yield "meta", meta
        except Exception as e:
            yield "error", handle_tweepy_exception(e)