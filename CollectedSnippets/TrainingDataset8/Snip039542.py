def hash_engine(*args, **kwargs):
    return get_hash(db.create_engine(*args, **kwargs))