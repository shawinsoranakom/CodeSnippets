def read_model_required_list_str(p: Annotated[FormModelRequiredListStr, Form()]):
    return {"p": p.p}