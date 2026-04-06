async def request_validation_handler(request: Request, exc: RequestValidationError):
    captured_exception.capture(exc)
    raise exc