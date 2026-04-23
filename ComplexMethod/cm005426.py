def get_reporting_integration_callbacks(report_to):
    if report_to is None:
        return []

    if isinstance(report_to, str):
        if report_to == "none":
            return []
        elif report_to == "all":
            report_to = get_available_reporting_integrations()
        else:
            report_to = [report_to]

    for integration in report_to:
        if integration not in INTEGRATION_TO_CALLBACK:
            raise ValueError(
                f"{integration} is not supported, only {', '.join(INTEGRATION_TO_CALLBACK.keys())} are supported."
            )

    return [INTEGRATION_TO_CALLBACK[integration] for integration in report_to]