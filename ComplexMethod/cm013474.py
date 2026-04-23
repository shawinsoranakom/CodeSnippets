def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            from torch.fx.experimental.symbolic_shapes import ShapeEnv

            if not isinstance(args[0], ShapeEnv):
                raise AssertionError(f"Expected ShapeEnv, got {type(args[0])}")

            global NEST

            trace_shape_events_log.debug(
                "%scall %s(*%r, **%r)", " " * NEST, name, args[1:], kwargs
            )
            NEST += 1

            def retlog(r: _R) -> _R:
                trace_shape_events_log.debug("%s-> %s", " " * (NEST - 1), r)
                return r

            shape_env = args[0]

            try:
                if not shape_env.should_record_events or shape_env.is_recording:  # type: ignore[has-type]
                    # If ShapeEnv is already recording an event, call the wrapped
                    # function directly.
                    #
                    # NB: here, we skip the check of whether all ShapeEnv instances
                    # are equal, in favor of a faster dispatch.
                    return retlog(fn(*args, **kwargs))

                # Retrieve an instance of ShapeEnv.
                # Assumption: the collection of args and kwargs may not reference
                # different ShapeEnv instances.
                self = _extract_shape_env_and_assert_equal(args, kwargs)

                # If we are calling this function without any ShapeEnv instance
                # alive in its arguments, we don't record and call the original.
                if self is None:
                    return retlog(fn(*args, **kwargs))

                # Otherwise, start recording and call the function.
                with self._recording():
                    # Take a snapshot of the current tracked_fakes.
                    tracked_fakes = (
                        self._snapshot_tracked_fakes() if save_tracked_fakes else None
                    )
                    # Record the event for 'fn'.
                    event = ShapeEnvEvent(
                        fn,
                        list(args),
                        kwargs,
                        tracked_fakes,
                        name=name,
                    )
                    # Play the event on this ShapeEnv.
                    # NB: It's important to put the event first, because running
                    # the event can trigger internal events that must be ordered
                    # after this event.  However, if an exception happens, we do
                    # NOT want to have the event in the list, so pop it off from
                    # the record if an error happened
                    self.events.append(event)
                    try:
                        return retlog(event.run(self))
                    except Exception:
                        self.events.pop()
                        raise

            except Exception:
                if not shape_env.should_record_events or shape_env.is_recording:
                    # If ShapeEnv is disabled or already recording an event, re-raise the exception without logging.
                    raise
                log.error(
                    "failed while running %s(*%s, **%s)",
                    name,
                    args[1:],
                    kwargs,
                    exc_info=log.isEnabledFor(logging.INFO),
                )
                raise

            finally:
                NEST -= 1