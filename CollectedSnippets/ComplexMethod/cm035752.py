def test_kubernetes_config_custom_values():
    """Test that KubernetesConfig accepts custom values."""
    config = KubernetesConfig(
        namespace='test-ns',
        ingress_domain='test.example.com',
        pvc_storage_size='5Gi',
        pvc_storage_class='fast',
        resource_cpu_request='2',
        resource_memory_request='2Gi',
        resource_memory_limit='4Gi',
        image_pull_secret='pull-secret',
        ingress_tls_secret='tls-secret',
        node_selector_key='zone',
        node_selector_val='us-east-1',
        tolerations_yaml='- key: special\n  value: true',
        privileged=True,
    )

    assert config.namespace == 'test-ns'
    assert config.ingress_domain == 'test.example.com'
    assert config.pvc_storage_size == '5Gi'
    assert config.pvc_storage_class == 'fast'
    assert config.resource_cpu_request == '2'
    assert config.resource_memory_request == '2Gi'
    assert config.resource_memory_limit == '4Gi'
    assert config.image_pull_secret == 'pull-secret'
    assert config.ingress_tls_secret == 'tls-secret'
    assert config.node_selector_key == 'zone'
    assert config.node_selector_val == 'us-east-1'
    assert config.tolerations_yaml == '- key: special\n  value: true'
    assert config.privileged is True