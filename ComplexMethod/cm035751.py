def test_kubernetes_config_defaults():
    """Test that KubernetesConfig has correct default values."""
    config = KubernetesConfig()
    assert config.namespace == 'default'
    assert config.ingress_domain == 'localhost'
    assert config.pvc_storage_size == '2Gi'
    assert config.pvc_storage_class is None
    assert config.resource_cpu_request == '1'
    assert config.resource_memory_request == '1Gi'
    assert config.resource_memory_limit == '2Gi'
    assert config.image_pull_secret is None
    assert config.ingress_tls_secret is None
    assert config.node_selector_key is None
    assert config.node_selector_val is None
    assert config.tolerations_yaml is None
    assert config.privileged is False