async def aget_object_or_404(klass, *args, **kwargs):
    """See get_object_or_404()."""
    queryset = _get_queryset(klass)
    if not hasattr(queryset, "aget"):
        klass__name = (
            klass.__name__ if isinstance(klass, type) else klass.__class__.__name__
        )
        raise ValueError(
            "First argument to aget_object_or_404() must be a Model, Manager, or "
            f"QuerySet, not '{klass__name}'."
        )
    try:
        return await queryset.aget(*args, **kwargs)
    except queryset.model.DoesNotExist:
        raise Http404(
            _("No %s matches the given query.") % queryset.model._meta.object_name
        )