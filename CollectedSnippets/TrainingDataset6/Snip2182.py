def foo(req: Model) -> dict[str, str | None]:
        return {
            "value": req.value or None,
            "embedded_value": req.embedded_model.value or None,
        }