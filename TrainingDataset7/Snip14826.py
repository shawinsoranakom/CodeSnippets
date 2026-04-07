def csrf_exempt(view_func):
    """Mark a view function as being exempt from the CSRF view protection."""

    # view_func.csrf_exempt = True would also work, but decorators are nicer
    # if they don't have side effects, so return a new function.

    if iscoroutinefunction(view_func):

        async def _view_wrapper(request, *args, **kwargs):
            return await view_func(request, *args, **kwargs)

    else:

        def _view_wrapper(request, *args, **kwargs):
            return view_func(request, *args, **kwargs)

    _view_wrapper.csrf_exempt = True

    return wraps(view_func)(_view_wrapper)