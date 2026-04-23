async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        **kwargs
    ) -> AsyncResult:
        auth_result: AuthResult = None
        cache_file = cls.get_cache_file()
        try:
            auth_result = cls.get_auth_result()
            response = to_async_iterator(cls.create_authed(model, messages, **kwargs, auth_result=auth_result))
            if "stream_timeout" in kwargs or "timeout" in kwargs:
                timeout = kwargs.get("stream_timeout") if cls.use_stream_timeout else kwargs.get("timeout")
                while True:
                    try:
                        yield await asyncio.wait_for(
                            response.__anext__(),
                            timeout=timeout
                        )
                    except TimeoutError as e:
                        raise TimeoutError("The operation timed out after {} seconds in {}".format(timeout, cls.__name__)) from e
                    except StopAsyncIteration:
                        break
            else:
                async for chunk in response:
                    yield chunk
        except (MissingAuthError, NoValidHarFileError, CloudflareError):
            # if cache_file.exists():
            #     cache_file.unlink()
            response = cls.on_auth_async(**kwargs)
            async for chunk in response:
                if isinstance(chunk, AuthResult):
                    auth_result = chunk
                else:
                    yield chunk
            response = to_async_iterator(cls.create_authed(model, messages, **kwargs, auth_result=auth_result))
            async for chunk in response:
                if cache_file is not None:
                    cls.write_cache_file(cache_file, auth_result)
                    cache_file = None
                yield chunk