def to_sync_generator(generator: AsyncIterator, stream: bool = True, timeout: int = None) -> Iterator:
    loop = get_running_loop(check_nested=False)
    if asyncio.iscoroutine(generator):
        if loop is not None:
            try:
                result = loop.run_until_complete(generator)
            except RuntimeError as e:
                if asyncio.iscoroutine(generator):
                    try:
                        generator.close()
                    except Exception:
                        pass
                raise NestAsyncioError(
                    'Install "nest-asyncio2" package | pip install -U nest-asyncio2'
                ) from e
        else:
            result = asyncio.run(generator)
        yield result
        return
    if not stream:
        yield from asyncio.run(async_generator_to_list(generator))
        return
    new_loop = False
    if loop is None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        new_loop = True
    gen = generator.__aiter__()
    try:
        while True:
            yield loop.run_until_complete(await_callback(gen.__anext__, timeout))
    except StopAsyncIteration:
        pass
    finally:
        if new_loop:
            try:
                runners._cancel_all_tasks(loop)
                loop.run_until_complete(loop.shutdown_asyncgens())
                if hasattr(loop, "shutdown_default_executor"):
                    loop.run_until_complete(loop.shutdown_default_executor())
            finally:
                asyncio.set_event_loop(None)
                loop.close()