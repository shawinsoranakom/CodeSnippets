async def async_search_media(
        self,
        query: SearchMediaQuery,
    ) -> SearchMedia:
        """Search the media player."""

        _valid_type_list = [
            key
            for key in self._browse_data.content_type_media_class
            if key not in ["apps", "app", "radios", "radio"]
        ]

        _media_content_type_list = (
            query.media_content_type.lower().replace(", ", ",").split(",")
            if query.media_content_type
            else ["albums", "tracks", "artists", "genres", "playlists"]
        )

        if query.media_content_type and set(_media_content_type_list).difference(
            _valid_type_list
        ):
            _LOGGER.debug("Invalid Media Content Type: %s", query.media_content_type)

            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_search_media_content_type",
                translation_placeholders={
                    "media_content_type": ", ".join(_valid_type_list)
                },
            )

        search_response_list: list[BrowseMedia] = []

        for _content_type in _media_content_type_list:
            payload = {
                "search_type": _content_type,
                "search_id": query.media_content_id,
                "search_query": query.search_query,
            }

            try:
                search_response_list.append(
                    await build_item_response(
                        self,
                        self._player,
                        payload,
                        self.browse_limit,
                        self._browse_data,
                    )
                )
            except BrowseError:
                _LOGGER.debug("Search Failure: Payload %s", payload)

        result: list[BrowseMedia] = []

        for search_response in search_response_list:
            # Apply the media_filter_classes to the result if specified
            if query.media_filter_classes and search_response.children:
                search_response.children = [
                    child
                    for child in search_response.children
                    if child.media_content_type in query.media_filter_classes
                ]
            if search_response.children:
                result.extend(list(search_response.children))

        return SearchMedia(result=result)