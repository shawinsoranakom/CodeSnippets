def test_exception_hierarchy_is_preserved() -> None:
    # DeploymentServiceError is the common root
    assert issubclass(DeploymentError, DeploymentServiceError)
    assert issubclass(AuthenticationError, DeploymentServiceError)
    assert issubclass(AuthorizationError, DeploymentServiceError)

    # AuthenticationError is a sibling of DeploymentError, NOT a child
    assert not issubclass(AuthenticationError, DeploymentError)
    assert not issubclass(AuthorizationError, DeploymentError)
    assert not issubclass(DeploymentError, AuthenticationError)
    assert not issubclass(DeploymentError, AuthorizationError)

    # Auth subtypes
    assert issubclass(CredentialResolutionError, AuthenticationError)
    assert issubclass(AuthSchemeError, AuthenticationError)

    # Deployment operation subtypes
    assert issubclass(ResourceConflictError, DeploymentError)
    assert issubclass(InvalidContentError, DeploymentError)
    assert issubclass(InvalidDeploymentOperationError, DeploymentError)
    assert issubclass(ResourceNotFoundError, DeploymentError)
    assert issubclass(DeploymentNotFoundError, ResourceNotFoundError)
    assert issubclass(DeploymentNotConfiguredError, DeploymentError)
    assert issubclass(OperationNotSupportedError, DeploymentError)