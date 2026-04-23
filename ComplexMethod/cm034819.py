def create():
            try:
                web_search = request.args.get("web_search")
                if web_search:
                    is_true_web_search = web_search.lower() in ["true", "1"]
                    web_search = True if is_true_web_search else web_search
                do_filter = request.args.get("filter_markdown", request.args.get("json"))
                cache_id = request.args.get('cache')
                model, provider_handler = get_model_and_provider(
                    request.args.get("model"), request.args.get("provider", request.args.get("audio_provider")),
                    stream=request.args.get("stream") and not do_filter and not cache_id,
                    ignore_stream=not request.args.get("stream"),
                )
                parameters = {
                    "model": model,
                    "messages": [{"role": "user", "content": request.args.get("prompt")}],
                    "stream": not do_filter and not cache_id,
                    "web_search": web_search,
                }
                if request.args.get("audio_provider") or request.args.get("audio"):
                    parameters["audio"] = {}
                def cast_str(response):
                    buffer = next(response)
                    while isinstance(buffer, (Reasoning, HiddenResponse, JsonResponse)):
                        buffer = next(response)
                    if isinstance(buffer, MediaResponse):
                        if len(buffer.get_list()) == 1:
                            if not cache_id:
                                return buffer.get_list()[0]
                        return "\n".join(asyncio.run(copy_media(
                            buffer.get_list(),
                            buffer.get("cookies"),
                            buffer.get("headers"),
                            alt=buffer.alt
                        )))
                    elif isinstance(buffer, AudioResponse):
                        return buffer.data
                    def iter_response():
                        yield str(buffer)
                        for chunk in response:
                            if isinstance(chunk, FinishReason):
                                yield f"[{chunk.reason}]" if chunk.reason != "stop" else ""
                            elif not isinstance(chunk, (Exception, JsonResponse)):
                                chunk = str(chunk)
                                if chunk:
                                    yield chunk
                    return iter_response()

                if cache_id:
                    cache_id = sha256(cache_id.encode() + json.dumps(parameters, sort_keys=True).encode()).hexdigest()
                    cache_dir = Path(get_cookies_dir()) / ".scrape_cache" / "create"
                    cache_file = cache_dir / f"{quote_plus(request.args.get('prompt', '').strip()[:20])}.{cache_id}.txt"
                    response = None
                    if cache_file.exists():
                        with cache_file.open("r") as f:
                            response = f.read()
                    if not response:
                        response = iter_run_tools(provider_handler, **parameters)
                        response = cast_str(response)
                        response = response if isinstance(response, str) else "".join(response)
                        if response:
                            cache_dir.mkdir(parents=True, exist_ok=True)
                            with cache_file.open("w") as f:
                                f.write(response)
                else:
                    response = cast_str(iter_run_tools(provider_handler, **parameters))
                if isinstance(response, str) and "\n" not in response:
                    if response.startswith("/media/"):
                        media_dir = get_media_dir()
                        filename = os.path.basename(response.split("?")[0])
                        if not cache_id:
                            try:
                                return send_from_directory(os.path.abspath(media_dir), filename)
                            finally:
                                os.remove(os.path.join(media_dir, filename))
                        else:
                            return redirect(response)
                    elif response.startswith("https://") or response.startswith("http://"):
                        return redirect(response)
                if do_filter:
                    is_true_filter = do_filter.lower() in ["true", "1"]
                    response = response if isinstance(response, str) else "".join(response)
                    return Response(filter_markdown(response, None if is_true_filter else do_filter, response if is_true_filter else ""), mimetype='text/plain')
                return Response(response, mimetype='text/plain')
            except (ModelNotFoundError, ProviderNotFoundError) as e:
                return jsonify({"error": {"message": f"{type(e).__name__}: {e}"}}), 404
            except MissingAuthError as e:
                return jsonify({"error": {"message": f"{type(e).__name__}: {e}"}}), 401
            except RateLimitError as e:
                return jsonify({"error": {"message": f"{type(e).__name__}: {e}"}}), 429
            except Exception as e:
                logger.exception(e)
                return jsonify({"error": {"message": f"{type(e).__name__}: {e}"}}), 500