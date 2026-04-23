async def generate_speech(
            config: AudioSpeechConfig,
            provider: Optional[str] = None,
            credentials: Annotated[HTTPAuthorizationCredentials, Depends(Api.security)] = None
        ):
            api_key = None
            if credentials is not None and credentials.credentials != "secret":
                api_key = credentials.credentials
            if provider is None:
                provider = config.provider
            if provider is None:
                provider = AppConfig.media_provider
            try:
                provider = ProviderUtils.get_by_label(provider)
            except ValueError as e:
                return ErrorResponse.from_message(str(e), 404)
            try:
                audio = filter_none(voice=config.voice, format=config.response_format, language=config.language)
                response = await self.client.chat.completions.create(
                    messages=[
                        {"role": "user", "content": f"{config.instrcutions} Text: {config.input}"}
                    ],
                    model=config.model,
                    provider=provider,
                    prompt=config.input,
                    api_key=api_key,
                    download_media=config.download_media,
                    **filter_none(
                        audio=audio if audio else None,
                    )
                )
                if response.choices[0].message.audio is not None:
                    response = base64.b64decode(response.choices[0].message.audio.data)
                    return Response(response, media_type=f"audio/{config.response_format.replace('mp3', 'mpeg')}")
                elif isinstance(response.choices[0].message.content, AudioResponse):
                    response = response.choices[0].message.content.data
                    response = response.replace("/media", get_media_dir())
                    def delete_file():
                        try:
                            os.remove(response)
                        except Exception as e:
                            logger.exception(e)
                    return FileResponse(response, background=BackgroundTask(delete_file))
            except (ModelNotFoundError, ProviderNotFoundError) as e:
                logger.exception(e)
                return ErrorResponse.from_exception(e, None, HTTP_404_NOT_FOUND)
            except MissingAuthError as e:
                logger.exception(e)
                return ErrorResponse.from_exception(e, None, HTTP_401_UNAUTHORIZED)
            except Exception as e:
                logger.exception(e)
                return ErrorResponse.from_exception(e, None, HTTP_500_INTERNAL_SERVER_ERROR)