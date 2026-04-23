async def pa_backend_conversation():
            """GUI-compatible streaming conversation endpoint for PA providers.

            Accepts the same JSON body as ``/backend-api/v2/conversation`` and
            streams Server-Sent Events in the same format used by the gpt4free
            web interface (``{"type": "content", "content": "..."}`` etc.).

            The ``provider`` field should contain the opaque PA provider ID
            returned by ``GET /pa/providers``.  When omitted the first available
            PA provider is used.
            """
            from g4f.mcp.pa_provider import get_pa_registry

            if app.demo and has_crypto:
                secret = request.headers.get("x-secret", request.headers.get("x_secret"))
                if not secret or not validate_secret(secret):
                    return jsonify({"error": {"message": "Invalid or missing secret"}}), 403

            try:
                body = {**request.json}
            except Exception:
                return jsonify({"error": {"message": "Invalid JSON body"}}), 422

            registry = get_pa_registry()
            pid = body.get("provider")
            if pid:
                provider_cls = registry.get_provider_class(pid)
                if provider_cls is None:
                    return jsonify({"error": {"message": f"PA provider '{pid}' not found"}}), 404
            else:
                listing = registry.list_providers()
                if not listing:
                    return jsonify({"error": {"message": "No PA providers found in workspace"}}), 404
                provider_cls = registry.get_provider_class(listing[0]["id"])

            provider_label = getattr(provider_cls, "label", provider_cls.__name__)
            messages = body.get("messages") or []
            model = body.get("model") or getattr(provider_cls, "default_model", "") or ""

            def gen_backend_stream():
                yield (
                    "data: "
                    + json.dumps({"type": "provider", "provider": {"name": pid, "label": provider_label, "model": model}})
                    + "\n\n"
                )
                try:
                    provider = provider_cls()
                    provider.__name__ = provider_cls.__name__
                    response = self.client.chat.completions.create(
                        messages=messages,
                        model=model,
                        provider=provider,
                        stream=True,
                    )
                    for chunk in response:
                        if chunk.choices[0].delta.content:
                            yield f"data: {json.dumps({'type': 'content', 'content': str(chunk.choices[0].delta.content)})}\n\n"
                except GeneratorExit:
                    pass
                except Exception as e:
                    logger.exception(e)
                    yield (
                        "data: "
                        + json.dumps({"type": "error", "error": f"{type(e).__name__}: {e}"})
                        + "\n\n"
                    )
                yield (
                    "data: "
                    + json.dumps({"type": "finish", "finish": "stop"})
                    + "\n\n"
                )

            return self.app.response_class(
                safe_iter_generator(gen_backend_stream()),
                mimetype='text/event-stream'
            )