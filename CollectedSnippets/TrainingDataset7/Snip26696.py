def get_response(req):
                file_resp = FileResponse(file1)
                file_resp["Content-Type"] = "text/html; charset=UTF-8"
                return file_resp