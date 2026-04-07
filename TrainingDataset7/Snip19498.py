def tagged_system_check(**kwargs):
    tagged_system_check.kwargs = kwargs
    return [checks.Warning("System Check")]