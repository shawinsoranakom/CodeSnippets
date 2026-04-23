async def run(
        self,
        input_data: Input,
        *,
        credentials: TwitterCredentials,
        **kwargs,
    ) -> BlockOutput:
        try:
            ids, texts, user_ids, user_names, data, included, meta, next_token = (
                self.get_bookmarked_tweets(
                    credentials,
                    input_data.max_results,
                    input_data.pagination_token,
                    input_data.expansions,
                    input_data.media_fields,
                    input_data.place_fields,
                    input_data.poll_fields,
                    input_data.tweet_fields,
                    input_data.user_fields,
                )
            )
            if ids:
                yield "id", ids
            if texts:
                yield "text", texts
            if user_ids:
                yield "userId", user_ids
            if user_names:
                yield "userName", user_names
            if data:
                yield "data", data
            if included:
                yield "included", included
            if meta:
                yield "meta", meta
            if next_token:
                yield "next_token", next_token
        except Exception as e:
            yield "error", handle_tweepy_exception(e)