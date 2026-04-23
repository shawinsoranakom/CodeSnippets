async def run(
        self,
        input_data: Input,
        *,
        credentials: TwitterCredentials,
        **kwargs,
    ) -> BlockOutput:
        try:
            ids, usernames, data, includes, meta, next_token = self.get_muted_users(
                credentials,
                input_data.max_results,
                input_data.pagination_token,
                input_data.expansions,
                input_data.tweet_fields,
                input_data.user_fields,
            )
            if ids:
                yield "ids", ids
            if usernames:
                yield "usernames", usernames
            if next_token:
                yield "next_token", next_token
            if data:
                yield "data", data
            if includes:
                yield "includes", includes
            if meta:
                yield "meta", meta
        except Exception as e:
            yield "error", handle_tweepy_exception(e)