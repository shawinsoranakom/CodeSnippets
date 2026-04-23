def get_api_keys(
        self,
        context: RequestContext,
        position: String = None,
        limit: NullableInteger = None,
        name_query: String = None,
        customer_id: String = None,
        include_values: NullableBoolean = None,
        **kwargs,
    ) -> ApiKeys:
        # TODO: migrate API keys in our store
        moto_backend = get_moto_backend(context.account_id, context.region)
        api_keys = [api_key.to_json() for api_key in reversed(moto_backend.keys.values())]
        if not include_values:
            for api_key in api_keys:
                api_key.pop("value")

        if limit is not None:
            if limit < 1 or limit > 500:
                limit = None

        item_list = PaginatedList(api_keys)

        def token_generator(item):
            return md5(item["id"])

        def filter_function(item):
            return item["name"].startswith(name_query)

        paginated_list, next_token = item_list.get_page(
            token_generator=token_generator,
            next_token=position,
            page_size=limit,
            filter_function=filter_function if name_query else None,
        )

        return ApiKeys(items=paginated_list, position=next_token)