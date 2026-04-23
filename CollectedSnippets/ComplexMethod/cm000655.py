async def run(
        self,
        input_data: Input,
        *,
        credentials: TwitterCredentials,
        **kwargs,
    ) -> BlockOutput:
        try:
            list_data, included, meta, list_ids, list_names, next_token = (
                self.get_owned_lists(
                    credentials,
                    input_data.user_id,
                    input_data.max_results,
                    input_data.pagination_token,
                    input_data.expansions,
                    input_data.user_fields,
                    input_data.list_fields,
                )
            )

            if list_ids:
                yield "list_ids", list_ids
            if list_names:
                yield "list_names", list_names
            if next_token:
                yield "next_token", next_token
            if list_data:
                yield "data", list_data
            if included:
                yield "included", included
            if meta:
                yield "meta", meta

        except Exception as e:
            yield "error", handle_tweepy_exception(e)