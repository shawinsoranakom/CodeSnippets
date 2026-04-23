def http_user_agent(user_agent: dict | str | None = None) -> str:
    """
    Formats a user-agent string with basic info about a request.
    """
    ua = f"transformers/{__version__}; python/{sys.version.split()[0]}; session_id/{SESSION_ID}"
    if is_torch_available():
        ua += f"; torch/{get_torch_version()}"
    if constants.HF_HUB_DISABLE_TELEMETRY:
        return ua + "; telemetry/off"
    if is_training_run_on_sagemaker():
        ua += "; " + "; ".join(f"{k}/{v}" for k, v in define_sagemaker_information().items())
    # CI will set this value to True
    if os.environ.get("TRANSFORMERS_IS_CI", "").upper() in ENV_VARS_TRUE_VALUES:
        ua += "; is_ci/true"
    if isinstance(user_agent, dict):
        ua += "; " + "; ".join(f"{k}/{v}" for k, v in user_agent.items())
    elif isinstance(user_agent, str):
        ua += "; " + user_agent
    return ua