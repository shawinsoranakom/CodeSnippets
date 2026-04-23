def _propagate_op_sharding_dispatch_slow_path(
        self,
        op_call: torch._ops.OpOverload,
        args: tuple[object, ...],
        kwargs: dict[str, object],
        op_info: OpInfo,
        # The logic here is a bit messy.  There are several reasons why the
        # C++ fastpath may have bailed out.  If we just cache missed, we will
        # come here because we need to actually calculate the real thing.
        # There's no need to have a SECOND Python cache lookup; the C++ native
        # cache completely subsumes it.  But sometimes, we will have failed
        # to compute the cache key in C++ entirely.  In this case, we DO need
        # to do a cache lookup in Python, as the missing cache key in C++
        # means we don't have access to it all.  Furthermore, without duping
        # this function, we need to do the try_cache test inside of the
        # try-except block so that either case hits the inference mode /
        # exception rewrapping case.
        #
        # This should be cleaned up.  First, ensuring the C++ codepath can
        # always compute a key will be a big help.  Second, we should properly
        # fastpath inference mode composite implicit autograd so that you
        # don't have to throw an exception even in "fastpath".
        try_cache: bool,
    ) -> object:
        # NOTE: schema should always be populated when calling this function,
        # as it's only called from C++ after unwrap_to_op_info (create_schema=True).
        # See dispatchDTensorOp in python_variable.cpp line 1453-1460.
        if op_info.schema is None:
            raise AssertionError(
                "op_info.schema should not be None in sharding propagation. "
                "This function should only be called after unwrap_to_op_info."
            )
        try:
            # We have basically inlined propagate() here, but WITHOUT the
            # output_sharding assignment
            if try_cache and not _are_we_tracing():
                result = self.sharding_propagator.propagate_op_sharding(op_info.schema)
            else:
                result = self.sharding_propagator.propagate_op_sharding_non_cached(
                    op_info.schema
                )
            if logger.handlers and logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    "sharding_prop MISS (C++ fast path): %s -> %s",
                    op_info.schema,
                    # pyrefly: ignore [missing-attribute]
                    result.output_spec,
                )
            return result
        except NotImplementedError:
            if torch._C._dispatch_has_kernel_for_dispatch_key(
                op_call.name(), torch._C.DispatchKey.CompositeImplicitAutograd
            ):
                # When running under inference mode, CompositeImplicitAutograd ops show up in __torch_dispatch__,
                # so we manually decompose them, here
                out = op_call.decompose(*args, **kwargs)
                if out is NotImplemented:
                    raise AssertionError from None
                return out
            else:
                raise
        except Exception as e:
            raise RuntimeError(
                f"{e}\n\nSharding propagation failed for {op_info.schema or op_call}"
            ) from e