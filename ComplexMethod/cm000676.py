async def run(
        self,
        input_data: Input,
        *,
        credentials: TwitterCredentials,
        **kwargs,
    ) -> BlockOutput:
        try:
            ids, texts, data, included, meta, next_token = self.get_quote_tweets(
                credentials,
                input_data.tweet_id,
                input_data.max_results,
                input_data.exclude,
                input_data.pagination_token,
                input_data.expansions,
                input_data.media_fields,
                input_data.place_fields,
                input_data.poll_fields,
                input_data.tweet_fields,
                input_data.user_fields,
            )
            if ids:
                yield "ids", ids
            if texts:
                yield "texts", texts
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