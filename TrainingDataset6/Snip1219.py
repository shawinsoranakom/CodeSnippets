def post_data(body: DataInput):
    content = body.data.decode("utf-8")
    return {"description": body.description, "content": content}