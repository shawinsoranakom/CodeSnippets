def multivalue_dict_key_error(request):
    cooked_eggs = "".join(["s", "c", "r", "a", "m", "b", "l", "e", "d"])  # NOQA
    sauce = "".join(  # NOQA
        ["w", "o", "r", "c", "e", "s", "t", "e", "r", "s", "h", "i", "r", "e"]
    )
    try:
        request.POST["bar"]
    except Exception:
        exc_info = sys.exc_info()
        send_log(request, exc_info)
        return technical_500_response(request, *exc_info)