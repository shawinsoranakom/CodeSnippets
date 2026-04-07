def redirect(to, *args, permanent=False, preserve_request=False, **kwargs):
    """
    Return an HttpResponseRedirect to the appropriate URL for the arguments
    passed.

    The arguments could be:

        * A model: the model's `get_absolute_url()` function will be called.

        * A view name, possibly with arguments: `urls.reverse()` will be used
          to reverse-resolve the name.

        * A URL, which will be used as-is for the redirect location.

    Issues a temporary redirect by default. Set permanent=True to issue a
    permanent redirect. Set preserve_request=True to instruct the user agent
    to preserve the original HTTP method and body when following the redirect.
    """
    redirect_class = (
        HttpResponsePermanentRedirect if permanent else HttpResponseRedirect
    )
    return redirect_class(
        resolve_url(to, *args, **kwargs),
        preserve_request=preserve_request,
    )