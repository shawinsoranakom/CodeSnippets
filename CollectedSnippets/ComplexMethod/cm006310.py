def encode_user_id(user_id: UUID | str) -> str:
    # Handle UUID
    if isinstance(user_id, UUID):
        return f"uuid-{str(user_id).lower()}"[:253]

    # Convert string to lowercase
    user_id_ = str(user_id).lower()

    # If the user_id looks like an email, replace @ and . with allowed characters
    if "@" in user_id_ or "." in user_id_:
        user_id_ = user_id_.replace("@", "-at-").replace(".", "-dot-")

    # Encode the user_id to base64
    # encoded = base64.b64encode(user_id.encode("utf-8")).decode("utf-8")

    # Replace characters not allowed in Kubernetes names
    user_id_ = user_id_.replace("+", "-").replace("/", "_").rstrip("=")

    # Ensure the name starts with an alphanumeric character
    if not user_id_[0].isalnum():
        user_id_ = "a-" + user_id_

    # Truncate to 253 characters (Kubernetes name length limit)
    user_id_ = user_id_[:253]

    if not all(c.isalnum() or c in "-_" for c in user_id_):
        msg = f"Invalid user_id: {user_id_}"
        raise ValueError(msg)

    # Ensure the name ends with an alphanumeric character
    while not user_id_[-1].isalnum():
        user_id_ = user_id_[:-1]

    return user_id_