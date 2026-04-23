async def run(
        self,
        input_data: Input,
        *,
        credentials: TwitterCredentials,
        **kwargs,
    ) -> BlockOutput:
        try:
            data, included, meta, ids, names, usernames, next_token = (
                self.get_retweeters(
                    credentials,
                    input_data.tweet_id,
                    input_data.max_results,
                    input_data.pagination_token,
                    input_data.expansions,
                    input_data.tweet_fields,
                    input_data.user_fields,
                )
            )

            if ids:
                yield "ids", ids
            if names:
                yield "names", names
            if usernames:
                yield "usernames", usernames
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