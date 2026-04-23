async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        conversation: JsonConversation = None,
        media: MediaListType = None,
        proxy: str = None,
        timeout: int = None,
        **kwargs
    ) -> AsyncResult:
        prompt = get_last_user_message(messages)
        cache_file = cls.get_cache_file()
        args = cls.read_args(kwargs.get("lmarena_args", {}))
        grecaptcha = kwargs.pop("grecaptcha", "")
        _need_clear_cookies = False
        for _ in range(2):
            if args:
                pass
            elif has_nodriver:
                args, grecaptcha = await cls.get_args_from_nodriver(proxy, _need_clear_cookies)
            else:
                raise MissingRequirementsError("No auth file found and nodriver is not available.")

            if not cls._models_loaded:
                # change to async
                await cls.get_models_async()

            def get_mode_id(_model):
                model_id = None
                # if not model:
                #     model = cls.default_model
                if _model in cls.model_aliases:
                    _model = cls.model_aliases[_model]
                if _model in cls.text_models:
                    model_id = cls.text_models[_model]
                elif _model in cls.image_models:
                    model_id = cls.image_models[_model]
                elif _model in cls.video_models:
                    model_id = cls.video_models[_model]
                elif _model:
                    raise ModelNotFoundError(f"Model '{_model}' is not supported by LMArena provider.")
                return model_id

            modelA:str = model
            modelB:str = kwargs.get("modelB", "")
            modelAId = get_mode_id(modelA)
            modelBId = get_mode_id(modelB) if modelB else None
            if modelAId and modelBId:
                mode = "side-by-side"
            elif modelAId:
                mode = "direct"
            else:
                mode = "battle"
            if conversation and getattr(conversation, "evaluationSessionId", None):
                url = cls.post_to_evaluation.format(id=conversation.evaluationSessionId)
                evaluationSessionId = conversation.evaluationSessionId
            else:
                url = cls.create_evaluation
                evaluationSessionId = str(uuid7())
            is_image_model = modelA in cls.image_models
            userMessageId = str(uuid7())
            modelAMessageId = str(uuid7())
            modelBMessageId = str(uuid7())
            if not grecaptcha and has_nodriver:
                debug.log("No grecaptcha token found, obtaining new one...")
                args, grecaptcha = await cls.get_grecaptcha(args, proxy)
            files = await cls.prepare_images(args, media)
            data = {
                "id": evaluationSessionId,
                "mode": mode,
                "userMessageId": userMessageId,
                "modelAMessageId": modelAMessageId,
                "userMessage": {
                    "content": prompt,
                    "experimental_attachments": files,
                    "metadata": {}
                },
                "modality": "image" if is_image_model else "chat",
                "recaptchaV3Token": grecaptcha
            }
            if modelAId:
                data["modelAId"] = modelAId
            if modelBId:
                data["modelBId"] = modelBId
            if mode in ["side-by-side", "battle"]:
                data["modelBMessageId"] = modelBMessageId

            yield JsonRequest.from_dict(data)
            try:
                async with StreamSession(**args, timeout=timeout or 5 * 60) as session:
                    async with session.post(
                            url,
                            json=data,
                            proxy=proxy,
                    ) as response:
                        await raise_for_status(response)
                        args["cookies"] = merge_cookies(args["cookies"], response)
                        async for chunk in response.iter_lines():
                            line = chunk.decode()
                            yield PlainTextResponse(line)
                            if line.startswith("a0:"):
                                chunk = json.loads(line[3:])
                                if chunk == "hasArenaError":
                                    raise ModelNotFoundError("LMArena Beta encountered an error: hasArenaError")
                                yield chunk
                            elif line.startswith("b0:"):
                                ...
                            elif line.startswith("ag:"):
                                chunk = json.loads(line[3:])
                                yield Reasoning(chunk)
                            elif (line.startswith("a2:") or line.startswith("b2:")) and line == 'a2:[{"type":"heartbeat"}]':
                                # 'a2:[{"type":"heartbeat"}]'
                                continue
                            elif line.startswith("a2:"):
                                chunk = json.loads(line[3:])
                                __images = [image.get("image") for image in chunk if image.get("image")]
                                if __images:
                                    yield ImageResponse(__images, prompt, {"model": modelA})

                            elif line.startswith("b2:"):
                                chunk = json.loads(line[3:])
                                __images = [image.get("image") for image in chunk if image.get("image")]
                                if __images:
                                    yield ImageResponse(__images, prompt, {"model": modelB})

                            elif line.startswith("ad:"):
                                yield JsonConversation(evaluationSessionId=evaluationSessionId)
                                finish = json.loads(line[3:])
                                if "finishReason" in finish:
                                    yield FinishReason(finish["finishReason"])
                                if "usage" in finish:
                                    yield Usage(**finish["usage"])
                            elif line.startswith("bd:"):
                                ...
                            elif line.startswith("a3:"):
                                raise RuntimeError(f"LMArena: {json.loads(line[3:])}")
                            elif line.startswith("b3:"):
                                ...
                            else:
                                debug.log(f"LMArena: Unknown line prefix: {line[:2]}")
                break
            except (CloudflareError, MissingAuthError) as error:
                args = None
                debug.error(error)
                debug.log(f"{cls.__name__}: Cloudflare error")
                continue
            except RateLimitError as error:
                args = None
                _need_clear_cookies = True
                debug.error(error)
                continue
            except:
                raise
        if args:
            debug.log("Save args to cache file:", str(cache_file))
            with cache_file.open("w") as f:
                f.write(json.dumps(args))