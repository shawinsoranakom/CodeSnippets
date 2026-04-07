def deployment_system_check(**kwargs):
    deployment_system_check.kwargs = kwargs
    return [checks.Warning("Deployment Check")]