def read_me(credentials: CredentialsDep):
    return {"message": "You are authenticated", "token": credentials.credentials}