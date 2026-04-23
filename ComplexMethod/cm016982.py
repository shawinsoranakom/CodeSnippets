def _friendly_http_message(status: int, body: Any) -> str:
    if status == 401:
        return "Unauthorized: Please login first to use this node."
    if status == 402:
        return "Payment Required: Please add credits to your account to use this node."
    if status == 409:
        return "There is a problem with your account. Please contact support@comfy.org."
    if status == 429:
        return "Rate Limit Exceeded: The server returned 429 after all retry attempts. Please wait and try again."
    try:
        if isinstance(body, dict):
            err = body.get("error")
            if isinstance(err, dict):
                msg = err.get("message")
                typ = err.get("type")
                if msg and typ:
                    return f"API Error: {msg} (Type: {typ})"
                if msg:
                    return f"API Error: {msg}"
            return f"API Error: {json.dumps(body)}"
        else:
            txt = str(body)
            if len(txt) <= 200:
                return f"API Error (raw): {txt}"
            return f"API Error (status {status})"
    except Exception:
        return f"HTTP {status}: Unknown error"