async def async_service_handler(service: ServiceCall) -> ServiceResponse:
            """Execute a shell command service."""
            payload = None
            if template_payload:
                payload = bytes(
                    template_payload.async_render(
                        variables=service.data, parse_result=False
                    ),
                    "utf-8",
                )

            request_url = template_url.async_render(
                variables=service.data, parse_result=False
            )

            headers = {}
            for header_name, template_header in template_headers.items():
                headers[header_name] = template_header.async_render(
                    variables=service.data, parse_result=False
                )

            if content_type:
                headers[hdrs.CONTENT_TYPE] = content_type

            _LOGGER.debug(
                "Calling %s %s with headers: %s and payload: %s",
                method,
                request_url,
                headers,
                payload,
            )

            try:
                # Prepare request kwargs
                request_kwargs = {
                    "data": payload,
                    "headers": headers or None,
                    "timeout": timeout,
                }

                # Add authentication
                if auth is not None:
                    request_kwargs["auth"] = auth
                elif digest_middleware is not None:
                    request_kwargs["middlewares"] = (digest_middleware,)

                async with getattr(websession, method)(
                    URL(request_url, encoded=skip_url_encoding),
                    **request_kwargs,
                ) as response:
                    if response.status < HTTPStatus.BAD_REQUEST:
                        _LOGGER.debug(
                            "Success. Url: %s. Status code: %d. Payload: %s",
                            response.url,
                            response.status,
                            payload,
                        )
                    else:
                        _LOGGER.warning(
                            "Error. Url: %s. Status code %d. Payload: %s",
                            response.url,
                            response.status,
                            payload,
                        )

                    if not service.return_response:
                        # always read the response to avoid closing the connection
                        # before the server has finished sending it, while avoiding excessive memory usage
                        async for _ in response.content.iter_chunked(1024):
                            pass

                        return None

                    _content = None
                    try:
                        if response.content_type == "application/json":
                            _content = await response.json()
                        else:
                            _content = await response.text()
                    except (JSONDecodeError, AttributeError) as err:
                        raise HomeAssistantError(
                            translation_domain=DOMAIN,
                            translation_key="decoding_error",
                            translation_placeholders={
                                "request_url": request_url,
                                "decoding_type": "JSON",
                            },
                        ) from err

                    except UnicodeDecodeError as err:
                        raise HomeAssistantError(
                            translation_domain=DOMAIN,
                            translation_key="decoding_error",
                            translation_placeholders={
                                "request_url": request_url,
                                "decoding_type": "text",
                            },
                        ) from err
                    return {
                        "content": _content,
                        "status": response.status,
                        "headers": dict(response.headers),
                    }

            except TimeoutError as err:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="timeout",
                    translation_placeholders={"request_url": request_url},
                ) from err

            except aiohttp.ClientError as err:
                _LOGGER.error("Error fetching data: %s", err)
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="client_error",
                    translation_placeholders={"request_url": request_url},
                ) from err