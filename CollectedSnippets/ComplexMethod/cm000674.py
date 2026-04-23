async def run(
        self,
        input_data: Input,
        *,
        credentials: TwitterCredentials,
        **kwargs,
    ) -> BlockOutput:
        try:
            ids, texts, data, included, meta, next_token = self.search_tweets(
                credentials,
                input_data.query,
                input_data.max_results,
                input_data.start_time,
                input_data.end_time,
                input_data.since_id,
                input_data.until_id,
                input_data.sort_order,
                input_data.pagination,
                input_data.expansions,
                input_data.media_fields,
                input_data.place_fields,
                input_data.poll_fields,
                input_data.tweet_fields,
                input_data.user_fields,
            )
            if ids:
                yield "tweet_ids", ids
            if texts:
                yield "tweet_texts", texts
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