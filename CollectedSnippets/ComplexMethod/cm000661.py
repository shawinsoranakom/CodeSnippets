async def run(
        self,
        input_data: Input,
        *,
        credentials: TwitterCredentials,
        **kwargs,
    ) -> BlockOutput:
        try:
            ids, texts, user_ids, user_names, data, included, meta, next_token = (
                self.get_liked_tweets(
                    credentials,
                    input_data.user_id,
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
                yield "ids", ids
            if texts:
                yield "texts", texts
            if user_ids:
                yield "userIds", user_ids
            if user_names:
                yield "userNames", user_names
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