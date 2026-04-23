async def run(
        self,
        input_data: Input,
        *,
        credentials: TwitterCredentials,
        **kwargs,
    ) -> BlockOutput:
        try:
            space_data, includes = self.get_space(
                credentials,
                input_data.space_id,
                input_data.expansions,
                input_data.space_fields,
                input_data.user_fields,
            )

            # Common outputs
            if space_data:
                if "id" in space_data:
                    yield "id", space_data.get("id")

                if "title" in space_data:
                    yield "title", space_data.get("title")

                if "host_ids" in space_data:
                    yield "host_ids", space_data.get("host_ids")

            if space_data:
                yield "data", space_data
            if includes:
                yield "includes", includes

        except Exception as e:
            yield "error", handle_tweepy_exception(e)