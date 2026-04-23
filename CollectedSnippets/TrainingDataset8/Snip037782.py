def get_or_create_cached_value():
            # Generate the key for the cached value. This is based on the
            # arguments passed to the function.
            value_key = _make_value_key(cached_func.cache_type, func, *args, **kwargs)

            try:
                result = cache.read_result(value_key)
                _LOGGER.debug("Cache hit: %s", func)

                replay_result_messages(result, cached_func.cache_type, func)

                return_value = result.value

            except CacheKeyNotFoundError:
                _LOGGER.debug("Cache miss: %s", func)

                with cached_func.warning_call_stack.calling_cached_function(func):
                    with cached_func.message_call_stack.calling_cached_function():
                        with cached_func.warning_call_stack.maybe_allow_widgets(
                            cached_func.allow_widgets
                        ):
                            with cached_func.message_call_stack.maybe_allow_widgets(
                                cached_func.allow_widgets
                            ):
                                with cached_func.warning_call_stack.maybe_suppress_cached_st_function_warning(
                                    cached_func.suppress_st_warning
                                ):
                                    return_value = func(*args, **kwargs)

                messages = cached_func.message_call_stack._most_recent_messages
                try:
                    cache.write_result(value_key, return_value, messages)
                except TypeError:
                    if type_util.is_type(
                        return_value, "snowflake.snowpark.dataframe.DataFrame"
                    ):

                        class UnevaluatedDataFrameError(StreamlitAPIException):
                            pass

                        raise UnevaluatedDataFrameError(
                            f"""
                            The function {get_cached_func_name_md(func)} is decorated with `st.experimental_memo` but it returns an unevaluated dataframe
                            of type `snowflake.snowpark.DataFrame`. Please call `collect()` or `to_pandas()` on the dataframe before returning it,
                            so `st.experimental_memo` can serialize and cache it."""
                        )
                    raise UnserializableReturnValueError(
                        return_value=return_value, func=cached_func.func
                    )

            return return_value