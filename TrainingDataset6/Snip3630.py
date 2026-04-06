def read_model_required_list_str(p: Annotated[QueryModelRequiredListStr, Query()]):
    return {"p": p.p}