def assert_sandbox_config(
    config: SandboxConfig,
    base_container_image=SandboxConfig.model_fields['base_container_image'].default,
    runtime_container_image='ghcr.io/openhands/runtime:mock-nikolaik',  # Default to mock version
    local_runtime_url=SandboxConfig.model_fields['local_runtime_url'].default,
    enable_auto_lint=False,
):
    """Helper function to assert the properties of the SandboxConfig object."""
    assert isinstance(config, SandboxConfig)
    assert config.base_container_image == base_container_image
    assert config.runtime_container_image == runtime_container_image
    assert config.enable_auto_lint is enable_auto_lint
    assert config.use_host_network is False
    assert config.timeout == 300
    assert config.local_runtime_url == local_runtime_url