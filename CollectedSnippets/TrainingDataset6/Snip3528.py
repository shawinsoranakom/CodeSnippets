def read_model_required_list_str(p: Annotated[HeaderModelRequiredListStr, Header()]):
    return {"p": p.p}