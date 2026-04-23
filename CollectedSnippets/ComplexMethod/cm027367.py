def _update_sources(self) -> None:
        """Update list of sources from current source, apps, inputs and configured list."""
        tv_state = self._client.tv_state
        source_list = self._source_list
        self._source_list = {}
        conf_sources = self._sources

        found_live_tv = False
        for app in tv_state.apps.values():
            if app["id"] == LIVE_TV_APP_ID:
                found_live_tv = True
            if app["id"] == tv_state.current_app_id:
                self._current_source = app["title"]
                self._source_list[app["title"]] = app
            elif (
                not conf_sources
                or app["id"] in conf_sources
                or any(word in app["title"] for word in conf_sources)
                or any(word in app["id"] for word in conf_sources)
            ):
                self._source_list[app["title"]] = app

        for source in tv_state.inputs.values():
            if source["appId"] == LIVE_TV_APP_ID:
                found_live_tv = True
            if source["appId"] == tv_state.current_app_id:
                self._current_source = source["label"]
                self._source_list[source["label"]] = source
            elif (
                not conf_sources
                or source["label"] in conf_sources
                or any(source["label"].find(word) != -1 for word in conf_sources)
            ):
                self._source_list[source["label"]] = source

        # empty list, TV may be off, keep previous list
        if not self._source_list and source_list:
            self._source_list = source_list
        # special handling of live tv since this might
        # not appear in the app or input lists in some cases
        elif not found_live_tv:
            app = {"id": LIVE_TV_APP_ID, "title": "Live TV"}
            if tv_state.current_app_id == LIVE_TV_APP_ID:
                self._current_source = app["title"]
                self._source_list["Live TV"] = app
            elif (
                not conf_sources
                or app["id"] in conf_sources
                or any(word in app["title"] for word in conf_sources)
                or any(word in app["id"] for word in conf_sources)
            ):
                self._source_list["Live TV"] = app