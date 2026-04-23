def get_webpo_content_binding(
    request: PoTokenRequest,
    webpo_clients=WEBPO_CLIENTS,
    bind_to_visitor_id=False,
) -> tuple[str | None, ContentBindingType | None]:

    client_name = traverse_obj(request.innertube_context, ('client', 'clientName'))
    if not client_name or client_name not in webpo_clients:
        return None, None

    if request.context == PoTokenContext.GVS and request._gvs_bind_to_video_id:
        return request.video_id, ContentBindingType.VIDEO_ID

    if request.context == PoTokenContext.GVS or client_name in ('WEB_REMIX', ):
        if request.is_authenticated:
            return request.data_sync_id, ContentBindingType.DATASYNC_ID
        else:
            if bind_to_visitor_id:
                visitor_id = _extract_visitor_id(request.visitor_data)
                if visitor_id:
                    return visitor_id, ContentBindingType.VISITOR_ID
            return request.visitor_data, ContentBindingType.VISITOR_DATA

    elif request.context in (PoTokenContext.PLAYER, PoTokenContext.SUBS):
        return request.video_id, ContentBindingType.VIDEO_ID

    return None, None