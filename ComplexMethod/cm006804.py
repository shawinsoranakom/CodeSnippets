async def get_knowledge_bases(kb_root: Path, user_id: UUID | str) -> list[str]:
    """Retrieve a list of available knowledge bases.

    Returns:
        A list of knowledge base names.
    """
    if not kb_root.exists():
        return []

    # Get the current user
    async with session_scope() as db:
        if not user_id:
            msg = "User ID is required for fetching knowledge bases."
            raise ValueError(msg)
        user_id = UUID(user_id) if isinstance(user_id, str) else user_id
        current_user = await get_user_by_id(db, user_id)
        if not current_user:
            msg = f"User with ID {user_id} not found."
            raise ValueError(msg)
        kb_user = current_user.username
    kb_path = kb_root / kb_user

    if not kb_path.exists():
        return []

    return [str(d.name) for d in kb_path.iterdir() if not d.name.startswith(".") and d.is_dir()]