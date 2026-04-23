def collective_rpc(  # type: ignore[override]
        self,
        method: str | Callable,
        timeout: float | None = None,
        args: tuple = (),
        kwargs: dict | None = None,
        non_block: bool = False,
        single_value: bool = False,
    ) -> Any:
        if kwargs is None:
            kwargs = {}

        if not non_block:
            result = run_method(self.driver_worker, method, args, kwargs)
            return result if single_value else [result]

        try:
            result = run_method(self.driver_worker, method, args, kwargs)
            if isinstance(result, AsyncModelRunnerOutput):
                if (async_thread := self.async_output_thread) is not None:
                    if single_value:
                        return async_thread.submit(result.get_output)

                    def get_output_list() -> list[Any]:
                        return [result.get_output()]

                    return async_thread.submit(get_output_list)
                result = result.get_output()
            future = Future[Any]()
            future.set_result(result if single_value else [result])
        except Exception as e:
            future = Future[Any]()
            future.set_exception(e)
        return future