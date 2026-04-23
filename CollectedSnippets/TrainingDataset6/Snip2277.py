def catching_dep() -> Any:
    try:
        yield "s"
    except CustomError as err:
        raise HTTPException(status_code=418, detail="Session error") from err