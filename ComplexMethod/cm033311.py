async def debug():
    req = await get_request_json()
    if not UserCanvasService.accessible(req["id"], current_user.id):
        return get_json_result(
            data=False, message='Only owner of canvas authorized for this operation.',
            code=RetCode.OPERATING_ERROR)
    try:
        e, user_canvas = UserCanvasService.get_by_id(req["id"])
        canvas = Canvas(json.dumps(user_canvas.dsl), current_user.id, canvas_id=user_canvas.id)
        canvas.reset()
        canvas.message_id = get_uuid()
        component = canvas.get_component(req["component_id"])["obj"]
        component.reset()

        if isinstance(component, LLM):
            component.set_debug_inputs(req["params"])
        component.invoke(**{k: o["value"] for k,o in req["params"].items()})
        outputs = component.output()
        for k in outputs.keys():
            if isinstance(outputs[k], partial):
                txt = ""
                iter_obj = outputs[k]()
                if inspect.isasyncgen(iter_obj):
                    async for c in iter_obj:
                        txt += c
                else:
                    for c in iter_obj:
                        txt += c
                outputs[k] = txt
        return get_json_result(data=outputs)
    except Exception as e:
        return server_error_response(e)