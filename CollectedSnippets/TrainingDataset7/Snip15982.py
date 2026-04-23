def download(modeladmin, request, selected):
    buf = StringIO("This is the content of the file")
    return StreamingHttpResponse(FileWrapper(buf))