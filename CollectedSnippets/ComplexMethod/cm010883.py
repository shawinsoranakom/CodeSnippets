def try_load(
        mod: torch.fx.GraphModule | torch._dynamo.utils.GmWrapper,
        args: list[Any],
        aot_config: AOTConfig,
        compiler_config_extra: CompilerConfigExtra | None,
        local: bool,
        remote: bool,
        compile_region_name: str | None = None,
    ) -> Callable[..., Any] | None:
        """
        Load a result from the cache, and reconstruct a runtime wrapper around the object
        """
        compiled_fn = None
        cache_info: dict[str, Any] = {}
        cache_key = None
        debug_lines: list[str] = []
        cache_event_time = time.time_ns()
        cache_state = None
        try:
            cache_key, debug_lines = autograd_cache_key(
                mod, args, aot_config, compiler_config_extra
            )
            result: tuple[GenericAOTAutogradResult[Any, Any], bytes] | None = (
                AOTAutogradCache._lookup(
                    cache_key, local, remote, args, cache_info, aot_config
                )
            )
            if result is not None:
                (entry, pickled_content) = result
                fx_config = create_fx_config(compiler_config_extra, compile_region_name)
                compiled_fn = entry.wrap_post_compile(args, aot_config, fx_config)
                # Make the compiled_fn serializable, where the serialize function just
                # makes a copy of the original entry before post compile via the pickled content
                compiled_fn = SerializableCompiledFunction(
                    compiled_fn, lambda: pickle.loads(pickled_content)
                )
                log.info("AOTAutograd cache hit for key %s", cache_key)

                counters["aot_autograd"]["autograd_cache_hit"] += 1
                cache_state = "hit"
                cache_event_time = time.time_ns()
                forward_time_saved = entry.forward_time_taken_ns // 1e6
                backward_time_saved = entry.backward_time_taken_ns // 1e6
                cache_info.update(
                    {
                        "forward_time_saved_ms": forward_time_saved,
                        "backward_time_saved_ms": backward_time_saved,
                        "time_saved_ms": forward_time_saved + backward_time_saved,
                    }
                )
                time_saved_ns = (
                    entry.forward_time_taken_ns + entry.backward_time_taken_ns
                )
                # TODO: should we use the same field for remote cache time saved for both
                # FXGraphCache and AOTAutogradCache?
                # get_metrics_context().increment(...)
                if (
                    ephemeral_increase
                    := add_ephemeral_timeout_increase_for_distributed(time_saved_ns)
                ) != 0:
                    cache_info["ephemeral_timeout_increase"] = ephemeral_increase

            if compiled_fn is None:
                log.info("AOTAutograd cache miss for key %s", cache_key)
                counters["aot_autograd"]["autograd_cache_miss"] += 1
                cache_state = "miss"
                cache_event_time = time.time_ns()
        # Count missing the FXGraphCache as a miss not a bypass
        except FXGraphCacheMiss as e:
            counters["aot_autograd"]["autograd_cache_miss"] += 1
            cache_state = "miss"
            if config.strict_autograd_cache or torch._dynamo.config.strict_precompile:
                raise e
        # Most often this is BypassAOTAutogradCache, but
        # if there's ever different reason we can't cache,
        # we still never want to hard throw an exception, since
        # we can always fallback to a cache bypass.
        # As an example, if the user calls autograd via
        # standalone inductor, we will sometimes get a GraphModule
        # that doesn't actually have a `.graph` on it. Instead
        # of checking every single case, we safely catch the exception
        # in those cases.
        except Exception as e:
            cache_key = None
            counters["aot_autograd"]["autograd_cache_bypass"] += 1
            log.info("Bypassing autograd cache due to: %s", e)
            cache_state = "bypass"
            cache_event_time = time.time_ns()
            cache_info["cache_bypass_reason"] = str(e)
            cache_info["cache_bypass_exception_type"] = type(e).__name__
            cache_info["cache_bypass_traceback"] = traceback.format_exc().split("\n")
            # TODO: this gets logged implicitly by cache_bypass_reason,
            # and here we explicitly log it into tlparse.
            # We may want to log this as an extra column in Scuba, though.
            cache_info["cache_bypass_hard_exception"] = not isinstance(
                e, BypassAOTAutogradCache
            )
            if remote:
                log_cache_bypass("bypass_aot_autograd", str(e))
            if config.strict_autograd_cache or torch._dynamo.config.strict_precompile:
                raise e
        if compiled_fn is None:
            # Set the cache key so we can save a cache result later
            symints = AOTAutogradCache._filter_backed_symints(args)
            if cache_key is not None:
                aot_config.cache_info = AOTAutogradCacheInfo(
                    cache_key,
                    time.time_ns(),
                    forward_symints=symints,
                )

        cache_info.update(
            {
                "key": cache_key,
                "cache_state": cache_state,
                "components": debug_lines,
            }
        )
        if chromium_event_log_active():
            CompileEventLogger.instant(
                f"autograd_cache_{cache_state}",
                metadata=cache_info,
                time_ns=cache_event_time,
            )
            CompileEventLogger.try_add_pt2_compile(
                "backend_compile",
                cache_state=cache_state,
                cache_event_time=cache_event_time,
                key=cache_info.get("key"),
                components=cache_info.get("components"),
                cache_bypass_reason=cache_info.get("cache_bypass_reason"),
                remote_cache_enabled=remote,
                local_cache_enabled=local,
            )

        torch._logging.trace_structured(
            "artifact",
            metadata_fn=lambda: {
                "name": f"aotautograd_cache_{cache_state}",
                "encoding": "json",
            },
            payload_fn=lambda: json.dumps(cache_info),
        )

        return compiled_fn