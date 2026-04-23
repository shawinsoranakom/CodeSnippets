async def get_model_a(name: str, model_c=Depends(get_model_c)):
        return {
            "name": name,
            "description": "model-a-desc",
            "foo": model_c,
            "tags": {"key1": "value1", "key2": "value2"},
        }