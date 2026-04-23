def read_current_user(credentials: HTTPBasicCredentials | None = Security(security)):
    if credentials is None:
        return {"msg": "Create an account first"}
    return {"username": credentials.username, "password": credentials.password}