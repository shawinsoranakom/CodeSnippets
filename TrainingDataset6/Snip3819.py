def no_response_model_annotation_union_return_model1() -> User | Item:
    return DBUser(name="John", surname="Doe", password_hash="secret")