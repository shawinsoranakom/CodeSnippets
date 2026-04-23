def _create_response_stream(self, kwargs: dict, provider: str, download_media: bool = True, tempfiles: list[str] = []) -> Iterator:
        def decorated_log(*values: str, file = None):
            debug.logs.append(" ".join([str(value) for value in values]))
            if debug.logging:
                debug.log_handler(*values, file=file)
        debug.log = decorated_log
        proxy = os.environ.get("G4F_PROXY")
        try:
            model, provider_handler = get_model_and_provider(
                kwargs.get("model"), provider or AnyProvider,
                has_images="media" in kwargs,
            )
            if "user" in kwargs:
                debug.error("User:", kwargs.get("user", "Unknown"))
                debug.error("Referrer:", kwargs.get("referer", ""))
                debug.error("User-Agent:", kwargs.get("user-agent", ""))
        except Exception as e:
            logger.exception(e)
            yield self._format_json('error', type(e).__name__, message=get_error_message(e))
            return
        if not isinstance(provider_handler, BaseRetryProvider):
            if not provider:
                provider = provider_handler.__name__
            yield self.handle_provider(provider_handler, model)
            if hasattr(provider_handler, "get_parameters"):
                yield self._format_json("parameters", provider_handler.get_parameters(as_json=True))
        try:
            result = iter_run_tools(provider_handler, **{**kwargs, "model": model, "download_media": download_media, "proxy": proxy})
            for chunk in result:
                if isinstance(chunk, ProviderInfo):
                    model = getattr(chunk, "model", model)
                    provider = getattr(chunk, "provider", provider)
                    yield self.handle_provider(chunk, model)
                elif isinstance(chunk, JsonConversation):
                    if provider is not None:
                        yield self._format_json("conversation", chunk.get_dict() if provider == "AnyProvider" else {
                            provider: chunk.get_dict()
                        })
                elif isinstance(chunk, Exception):
                    logger.exception(chunk)
                    yield self._format_json('message', get_error_message(chunk), error=type(chunk).__name__)
                elif isinstance(chunk, RequestLogin):
                    yield self._format_json("preview", chunk.to_string())
                elif isinstance(chunk, PreviewResponse):
                    yield self._format_json("preview", chunk.to_string())
                elif isinstance(chunk, ImagePreview):
                    yield self._format_json("preview", chunk.to_string(), urls=chunk.urls, alt=chunk.alt)
                elif isinstance(chunk, MediaResponse):
                    media = chunk
                    if download_media or chunk.get("cookies") or chunk.get("headers"):
                        chunk.alt = format_media_prompt(kwargs.get("messages"), chunk.alt)
                        width, height = get_width_height(chunk.get("width"), chunk.get("height"))
                        tags = [model, kwargs.get("aspect_ratio"), kwargs.get("resolution")]
                        media = asyncio.run(copy_media(
                            chunk.get_list(),
                            chunk.get("cookies"),
                            chunk.get("headers"),
                            proxy=proxy,
                            alt=chunk.alt,
                            tags=tags,
                            add_url=True,
                            timeout=kwargs.get("timeout"),
                            return_target=True if isinstance(chunk, ImageResponse) else False,
                        ))
                        options = {}
                        target_paths, urls = get_target_paths_and_urls(media)
                        if target_paths:
                            if has_pillow:
                                try:
                                    with Image.open(target_paths[0]) as img:
                                        width, height = img.size
                                        options = {"width": width, "height": height}
                                except Exception as e:
                                    logger.exception(e)
                            options["target_paths"] = target_paths
                        media = ImageResponse(urls, chunk.alt, options) if isinstance(chunk, ImageResponse) else VideoResponse(media, chunk.alt)
                    yield self._format_json("content", str(media), urls=media.urls, alt=media.alt)
                elif isinstance(chunk, SynthesizeData):
                    yield self._format_json("synthesize", chunk.get_dict())
                elif isinstance(chunk, TitleGeneration):
                    yield self._format_json("title", chunk.title)
                elif isinstance(chunk, Parameters):
                    yield self._format_json("parameters", chunk.get_dict())
                elif isinstance(chunk, FinishReason):
                    yield self._format_json("finish", chunk.get_dict())
                elif isinstance(chunk, Usage):
                    yield self._format_json("usage", chunk.get_dict(), model=model, provider=provider)
                elif isinstance(chunk, Reasoning):
                    yield self._format_json("reasoning", **chunk.get_dict())
                elif isinstance(chunk, YouTubeResponse):
                    yield self._format_json("content", chunk.to_string())
                elif isinstance(chunk, AudioResponse):
                    yield self._format_json("content", str(chunk), data=chunk.data)
                elif isinstance(chunk, SuggestedFollowups):
                    yield self._format_json("suggestions", chunk.suggestions)
                elif isinstance(chunk, DebugResponse):
                    yield self._format_json("log", chunk.log)
                elif isinstance(chunk, ContinueResponse):
                    yield self._format_json("continue", chunk.text)
                elif isinstance(chunk, VariantResponse):
                    yield self._format_json("variant", chunk.text)
                elif isinstance(chunk, ToolCalls):
                    yield self._format_json("tool_calls", chunk.list)
                elif isinstance(chunk, RawResponse):
                    yield self._format_json(chunk.type, **chunk.get_dict())
                elif isinstance(chunk, JsonRequest):
                    yield self._format_json("request", chunk.get_dict())
                elif isinstance(chunk, JsonResponse):
                    yield self._format_json("response", chunk.get_dict())
                elif isinstance(chunk, PlainTextResponse):
                    yield self._format_json("response", chunk.text)
                elif isinstance(chunk, HeadersResponse):
                    yield self._format_json("headers", chunk.get_dict())
                else:
                    yield self._format_json("content", str(chunk))
        except MissingAuthError as e:
            yield self._format_json('auth', type(e).__name__, message=get_error_message(e))
        except (TimeoutError, asyncio.exceptions.CancelledError) as e:
            if "user" in kwargs:
                debug.error(e, "User:", kwargs.get("user", "Unknown"))
            yield self._format_json('error', type(e).__name__, message=get_error_message(e))
        except Exception as e:
            if "user" in kwargs:
                debug.error(e, "User:", kwargs.get("user", "Unknown"))
            logger.exception(e)
            yield self._format_json('error', type(e).__name__, message=get_error_message(e))
        finally:
            yield from self._yield_logs()
            for tempfile in tempfiles:
                try:
                    os.remove(tempfile)
                except Exception as e:
                    logger.exception(e)