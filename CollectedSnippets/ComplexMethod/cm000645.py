async def run(
        self,
        input_data: Input,
        *,
        credentials: TwitterCredentials,
        **kwargs,
    ) -> BlockOutput:
        try:
            data, included, meta, ids, titles, host_ids, next_token = (
                self.search_spaces(
                    credentials,
                    input_data.query,
                    input_data.max_results,
                    input_data.state,
                    input_data.expansions,
                    input_data.space_fields,
                    input_data.user_fields,
                )
            )

            if ids:
                yield "ids", ids
            if titles:
                yield "titles", titles
            if host_ids:
                yield "host_ids", host_ids
            if next_token:
                yield "next_token", next_token
            if data:
                yield "data", data
            if included:
                yield "includes", included
            if meta:
                yield "meta", meta

        except Exception as e:
            yield "error", handle_tweepy_exception(e)