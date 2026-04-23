async def run(
        self,
        input_data: Input,
        *,
        credentials: TwitterCredentials,
        **kwargs,
    ) -> BlockOutput:
        try:
            ids, texts, user_ids, user_names, data, included, meta = self.get_tweets(
                credentials,
                input_data.tweet_ids,
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
            if user_ids:
                yield "userIds", user_ids
            if user_names:
                yield "userNames", user_names
            if data:
                yield "data", data
            if included:
                yield "included", included
            if meta:
                yield "meta", meta

        except Exception as e:
            yield "error", handle_tweepy_exception(e)