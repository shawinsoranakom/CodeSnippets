async def get_list_component_response_model(
        self,
        *,
        component_id: str | None = None,
        search: str | None = None,
        private: bool | None = None,
        tags: list[str] | None = None,
        is_component: bool | None = None,
        fields: list[str] | None = None,
        filter_by_user: bool = False,
        liked: bool = False,
        store_api_key: str | None = None,
        sort: list[str] | None = None,
        page: int = 1,
        limit: int = 15,
    ):
        async with user_data_context(api_key=store_api_key, store_service=self):
            filter_conditions: list[dict[str, Any]] = self.build_filter_conditions(
                component_id=component_id,
                search=search,
                private=private,
                tags=tags,
                is_component=is_component,
                filter_by_user=filter_by_user,
                liked=liked,
                store_api_key=store_api_key,
            )

            result: list[ListComponentResponse] = []
            authorized = False
            metadata: dict = {}
            comp_count = 0
            try:
                result, metadata = await self.query_components(
                    api_key=store_api_key,
                    page=page,
                    limit=limit,
                    sort=sort,
                    fields=fields,
                    filter_conditions=filter_conditions,
                    use_api_key=liked or filter_by_user,
                )
                if metadata:
                    comp_count = metadata.get("filter_count", 0)
            except HTTPStatusError as exc:
                if exc.response.status_code == httpx.codes.FORBIDDEN:
                    msg = "You are not authorized to access this public resource"
                    raise ForbiddenError(msg) from exc
                if exc.response.status_code == httpx.codes.UNAUTHORIZED:
                    msg = "You are not authorized to access this resource. Please check your API key."
                    raise APIKeyError(msg) from exc
            except Exception as exc:
                msg = f"Unexpected error: {exc}"
                raise ValueError(msg) from exc
            try:
                if result and not metadata:
                    if len(result) >= limit:
                        comp_count = await self.count_components(
                            api_key=store_api_key,
                            filter_conditions=filter_conditions,
                            use_api_key=liked or filter_by_user,
                        )
                    else:
                        comp_count = len(result)
                elif not metadata:
                    comp_count = 0
            except HTTPStatusError as exc:
                if exc.response.status_code == httpx.codes.FORBIDDEN:
                    msg = "You are not authorized to access this public resource"
                    raise ForbiddenError(msg) from exc
                if exc.response.status_code == httpx.codes.UNAUTHORIZED:
                    msg = "You are not authorized to access this resource. Please check your API key."
                    raise APIKeyError(msg) from exc

            if store_api_key:
                # Now, from the result, we need to get the components
                # the user likes and set the liked_by_user to True
                # if any of the components does not have an id, it means
                # we should not update the components

                if not result or any(component.id is None for component in result):
                    authorized = await self.check_api_key(store_api_key)
                else:
                    try:
                        updated_result = await update_components_with_user_data(
                            result, self, store_api_key, liked=liked
                        )
                        authorized = True
                        result = updated_result
                    except Exception:  # noqa: BLE001
                        logger.debug("Error updating components with user data", exc_info=True)
                        # If we get an error here, it means the user is not authorized
                        authorized = False
        return ListComponentResponseModel(results=result, authorized=authorized, count=comp_count)