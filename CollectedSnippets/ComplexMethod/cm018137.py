async def check_translations(
    ignore_missing_translations: str | list[str],
    ignore_translations_for_mock_domains: str | list[str],
    request: pytest.FixtureRequest,
) -> AsyncGenerator[None]:
    """Check that translation requirements are met.

    Current checks:
    - data entry flow results (ConfigFlow/OptionsFlow/RepairFlow)
    - issue registry entries
    - action (service) exceptions
    """
    if not isinstance(ignore_missing_translations, list):
        ignore_missing_translations = [ignore_missing_translations]

    if not isinstance(ignore_translations_for_mock_domains, list):
        ignored_domains = {ignore_translations_for_mock_domains}
    else:
        ignored_domains = set(ignore_translations_for_mock_domains)

    # Set all ignored translation keys to "unused"
    translation_errors = dict.fromkeys(ignore_missing_translations, "unused")

    translation_coros = set()

    # Keep reference to original functions
    _original_flow_manager_async_handle_step = FlowManager._async_handle_step
    _original_issue_registry_async_create_issue = ir.IssueRegistry.async_get_or_create
    _original_service_registry_async_call = ServiceRegistry.async_call
    _original_service_registry_async_register = ServiceRegistry.async_register

    # Prepare override functions
    async def _flow_manager_async_handle_step(
        self: FlowManager, flow: FlowHandler, *args
    ) -> FlowResult:
        result = await _original_flow_manager_async_handle_step(self, flow, *args)
        await _check_config_flow_result_translations(
            self, flow, result, translation_errors, ignored_domains
        )
        return result

    def _issue_registry_async_create_issue(
        self: ir.IssueRegistry, domain: str, issue_id: str, *args, **kwargs
    ) -> ir.IssueEntry:
        result = _original_issue_registry_async_create_issue(
            self, domain, issue_id, *args, **kwargs
        )
        translation_coros.add(
            _check_create_issue_translations(
                self, result, translation_errors, ignored_domains
            )
        )
        return result

    async def _service_registry_async_call(
        self: ServiceRegistry,
        domain: str,
        service: str,
        service_data: dict[str, Any] | None = None,
        blocking: bool = False,
        context: Context | None = None,
        target: dict[str, Any] | None = None,
        return_response: bool = False,
    ) -> ServiceResponse:
        try:
            return await _original_service_registry_async_call(
                self,
                domain,
                service,
                service_data,
                blocking,
                context,
                target,
                return_response,
            )
        except HomeAssistantError as err:
            translation_coros.add(
                _check_exception_translation(
                    self._hass,
                    err,
                    translation_errors,
                    request,
                    ignored_domains,
                )
            )
            raise

    @callback
    def _service_registry_async_register(
        self: ServiceRegistry,
        domain: str,
        service: str,
        service_func: Callable[
            [ServiceCall],
            Coroutine[Any, Any, ServiceResponse | EntityServiceResponse]
            | ServiceResponse
            | EntityServiceResponse
            | None,
        ],
        schema: VolSchemaType | None = None,
        supports_response: SupportsResponse = SupportsResponse.NONE,
        job_type: HassJobType | None = None,
        *,
        description_placeholders: Mapping[str, str] | None = None,
    ) -> None:
        if (
            (current_frame := inspect.currentframe()) is None
            or (caller := current_frame.f_back) is None
            or (
                # async_mock_service is used in tests to register test services
                caller.f_code.co_name != "async_mock_service"
                # ServiceRegistry.async_register can also be called directly in
                # a test module
                and not caller.f_code.co_filename.startswith(
                    str(Path(__file__).parents[0])
                )
            )
        ):
            translation_coros.add(
                _check_service_registration_translation(
                    self._hass,
                    domain,
                    service,
                    description_placeholders,
                    translation_errors,
                    ignored_domains,
                )
            )

        _original_service_registry_async_register(
            self,
            domain,
            service,
            service_func,
            schema,
            supports_response,
            job_type,
            description_placeholders=description_placeholders,
        )

    # Use override functions
    with (
        patch(
            "homeassistant.data_entry_flow.FlowManager._async_handle_step",
            _flow_manager_async_handle_step,
        ),
        patch(
            "homeassistant.helpers.issue_registry.IssueRegistry.async_get_or_create",
            _issue_registry_async_create_issue,
        ),
        patch(
            "homeassistant.core.ServiceRegistry.async_call",
            _service_registry_async_call,
        ),
        patch(
            "homeassistant.core.ServiceRegistry.async_register",
            _service_registry_async_register,
        ),
    ):
        yield

    await asyncio.gather(*translation_coros)

    # Run final checks
    unused_ignore = [k for k, v in translation_errors.items() if v == "unused"]
    if unused_ignore:
        # Some ignored translations were not used
        pytest.fail(
            f"Unused ignore translations: {', '.join(unused_ignore)}. "
            "Please remove them from the ignore_missing_translations fixture."
        )
    for description in translation_errors.values():
        if description != "used":
            pytest.fail(description)