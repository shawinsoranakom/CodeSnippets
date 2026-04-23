def post_union_form(data: Annotated[UserForm | CompanyForm, Form()]):
    return {"received": data}