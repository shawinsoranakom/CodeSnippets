def build_filter_conditions(
        self,
        *,
        component_id: str | None = None,
        search: str | None = None,
        private: bool | None = None,
        tags: list[str] | None = None,
        is_component: bool | None = None,
        filter_by_user: bool | None = False,
        liked: bool | None = False,
        store_api_key: str | None = None,
    ):
        filter_conditions = []

        if component_id is None:
            component_id = get_id_from_search_string(search) if search else None

        if search is not None and component_id is None:
            search_conditions = self.build_search_filter_conditions(search)
            filter_conditions.append(search_conditions)

        if private is not None:
            filter_conditions.append({"private": {"_eq": private}})

        if tags:
            tags_filter = self.build_tags_filter(tags)
            filter_conditions.append(tags_filter)
        if component_id is not None:
            filter_conditions.append({"id": {"_eq": component_id}})
        if is_component is not None:
            filter_conditions.append({"is_component": {"_eq": is_component}})
        if liked and store_api_key:
            liked_filter = self.build_liked_filter()
            filter_conditions.append(liked_filter)
        elif liked and not store_api_key:
            msg = "You must provide an API key to filter by likes"
            raise APIKeyError(msg)

        if filter_by_user and store_api_key:
            user_data = user_data_var.get()
            if not user_data:
                msg = "No user data"
                raise ValueError(msg)
            filter_conditions.append({"user_created": {"_eq": user_data["id"]}})
        elif filter_by_user and not store_api_key:
            msg = "You must provide an API key to filter your components"
            raise APIKeyError(msg)
        else:
            filter_conditions.append({"private": {"_eq": False}})

        return filter_conditions