async def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        aexa = AsyncExa(api_key=credentials.api_key.get_secret_value())

        sdk_webset = await aexa.websets.get(id=input_data.webset_id)

        status_str = (
            sdk_webset.status.value
            if hasattr(sdk_webset.status, "value")
            else str(sdk_webset.status)
        )

        searches_data = [
            s.model_dump(by_alias=True, exclude_none=True)
            for s in sdk_webset.searches or []
        ]
        enrichments_data = [
            e.model_dump(by_alias=True, exclude_none=True)
            for e in sdk_webset.enrichments or []
        ]
        monitors_data = [
            m.model_dump(by_alias=True, exclude_none=True)
            for m in sdk_webset.monitors or []
        ]

        yield "webset_id", sdk_webset.id
        yield "status", status_str
        yield "external_id", sdk_webset.external_id
        yield "searches", searches_data
        yield "enrichments", enrichments_data
        yield "monitors", monitors_data
        yield "metadata", sdk_webset.metadata or {}
        yield "created_at", (
            sdk_webset.created_at.isoformat() if sdk_webset.created_at else ""
        )
        yield "updated_at", (
            sdk_webset.updated_at.isoformat() if sdk_webset.updated_at else ""
        )