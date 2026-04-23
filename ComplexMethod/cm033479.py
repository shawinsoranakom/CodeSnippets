async def _fetch_datasets_page(
        self,
        *,
        api_key: str,
        page: int,
        page_size: int,
        orderby: str = "create_time",
        desc: bool = True,
        id: str | None = None,
        name: str | None = None,
    ):
        """Fetch one structured page of accessible datasets from the backend API."""
        params = {"page": page, "page_size": page_size, "orderby": orderby, "desc": desc}
        if id:
            params["id"] = id
        if name:
            params["name"] = name

        res = await self._get("/datasets", params, api_key=api_key)
        if not res or res.status_code != 200:
            error_message = None
            if res is not None:
                try:
                    error_message = res.json().get("message")
                except Exception:
                    error_message = None
            raise Exception([types.TextContent(type="text", text=error_message or "Cannot process this operation.")])

        res_json = res.json()
        if res_json.get("code") != 0:
            raise Exception([types.TextContent(type="text", text=res_json.get("message", "Cannot process this operation."))])

        return res_json