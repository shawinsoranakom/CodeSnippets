def post_form(user: Annotated[FormModel, Form()]):
    return user