async def run_pipeline(
        self,
        protocol_method: Callable[P, Iterator[T] | None | Awaitable[None]],
        *args,
        retry_limit: int = 3,
    ) -> list[T] | list[None]:
        method_name = protocol_method.__name__
        protocol_name = protocol_method.__qualname__.split(".")[0]
        protocol_class = getattr(protocols, protocol_name)
        if not issubclass(protocol_class, AgentComponent):
            raise TypeError(f"{repr(protocol_method)} is not a protocol method")

        # Clone parameters to revert on failure
        original_args = self._selective_copy(args)
        pipeline_attempts = 0
        method_result: list[T] = []
        self._trace.append(f"⬇️  {Fore.BLUE}{method_name}{Fore.RESET}")

        while pipeline_attempts < retry_limit:
            try:
                for component in self.components:
                    # Skip other protocols
                    if not isinstance(component, protocol_class):
                        continue

                    # Skip disabled components
                    if not component.enabled:
                        self._trace.append(
                            f"   {Fore.LIGHTBLACK_EX}"
                            f"{component.__class__.__name__}{Fore.RESET}"
                        )
                        continue

                    method = cast(
                        Callable[..., Iterator[T] | None | Awaitable[None]] | None,
                        getattr(component, method_name, None),
                    )
                    if not callable(method):
                        continue

                    component_attempts = 0
                    while component_attempts < retry_limit:
                        try:
                            component_args = self._selective_copy(args)
                            result = method(*component_args)
                            if inspect.isawaitable(result):
                                result = await result
                            if result is not None:
                                method_result.extend(result)
                            args = component_args
                            self._trace.append(f"✅ {component.__class__.__name__}")

                        except ComponentEndpointError:
                            self._trace.append(
                                f"❌ {Fore.YELLOW}{component.__class__.__name__}: "
                                f"ComponentEndpointError{Fore.RESET}"
                            )
                            # Retry the same component on ComponentEndpointError
                            component_attempts += 1
                            continue
                        # Successful component execution
                        break
                # Successful pipeline execution
                break
            except EndpointPipelineError as e:
                self._trace.append(
                    f"❌ {Fore.LIGHTRED_EX}{e.triggerer.__class__.__name__}: "
                    f"EndpointPipelineError{Fore.RESET}"
                )
                # Restart from the beginning on EndpointPipelineError
                # Revert to original parameters
                args = self._selective_copy(original_args)
                pipeline_attempts += 1
                continue  # Start the loop over
            except Exception as e:
                raise e
        return method_result