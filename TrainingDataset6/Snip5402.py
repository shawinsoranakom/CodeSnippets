async def response_validation_handler(_: Request, exc: ResponseValidationError):
    captured_exception.capture(exc)
    raise exc