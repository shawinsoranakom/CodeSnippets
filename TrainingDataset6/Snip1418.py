def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)