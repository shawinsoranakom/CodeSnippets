def raise_after_yield() -> Any:
    yield
    raise HTTPException(status_code=503, detail="Exception after yield")