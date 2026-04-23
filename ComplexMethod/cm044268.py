def log(
        self,
        user_settings: UserSettings,
        system_settings: SystemSettings,
        route: str,
        func: Callable,
        kwargs: dict[str, Any],
        exec_info: (
            tuple[type[BaseException], BaseException, TracebackType]
            | tuple[None, None, None]
        ),
        custom_headers: dict[str, Any] | None = None,
    ) -> None:
        """Log command output and relevant information.

        Parameters
        ----------
        user_settings : UserSettings
            User Settings object.
        system_settings : SystemSettings
            System Settings object.
        route : str
            Route for the command.
        func : Callable
            Callable representing the executed function.
        kwargs : Dict[str, Any]
            Keyword arguments passed to the function.
        exec_info : Union[
            Tuple[Type[BaseException], BaseException, TracebackType],
            Tuple[None, None, None],
        ]
            Exception information, by default None
        custom_headers : Optional[Dict[str, Any]]
            Custom headers to include in the log, by default None
        Returns
        -------
        None
        """
        self._user_settings = user_settings
        self._system_settings = system_settings
        self._logging_settings = LoggingSettings(
            user_settings=self._user_settings,
            system_settings=self._system_settings,
        )
        self._handlers_manager.update_handlers(self._logging_settings)

        if not self._logging_settings.logging_suppress:
            if "login" in route:
                self._log_startup(route, custom_headers)
            else:
                # Remove CommandContext if any
                kwargs.pop("cc", None)

                passed_model = kwargs.get("provider_choices", DummyProvider())
                provider = (
                    passed_model.provider
                    if hasattr(passed_model, "provider")
                    else "not_passed_to_kwargs"
                )

                # Truncate kwargs if too long
                kwargs = {k: str(v)[:300] for k, v in kwargs.items()}
                # Get execution info
                error = None if all(i is None for i in exec_info) else str(exec_info[1])

                # Construct message
                message_label = "ERROR" if error else "CMD"
                log_message = json.dumps(
                    {
                        "route": route,
                        "input": kwargs,
                        "error": error,
                        "provider": provider,
                        "custom_headers": custom_headers,
                    },
                    default=to_jsonable_python,
                )
                log_message = f"{message_label}: {log_message}"
                log_level = self._logger.error if error else self._logger.info
                log_level(
                    log_message,
                    extra={"func_name_override": func.__name__},
                    exc_info=exec_info,
                )