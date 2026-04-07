def sensitive_kwargs_function_caller(request):
    try:
        sensitive_kwargs_function(
            "".join(
                ["w", "o", "r", "c", "e", "s", "t", "e", "r", "s", "h", "i", "r", "e"]
            )
        )
    except Exception:
        exc_info = sys.exc_info()
        send_log(request, exc_info)
        return technical_500_response(request, *exc_info)