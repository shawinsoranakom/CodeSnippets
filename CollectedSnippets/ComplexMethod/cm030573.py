def handle(self, fn_name, action, *args, **kwds):
        self.parent.calls.append((self, fn_name, args, kwds))
        if action is None:
            return None
        elif action == "return self":
            return self
        elif action == "return response":
            res = MockResponse(200, "OK", {}, "")
            return res
        elif action == "return request":
            return Request("http://blah/")
        elif action.startswith("error"):
            code = action[action.rfind(" ")+1:]
            try:
                code = int(code)
            except ValueError:
                pass
            res = MockResponse(200, "OK", {}, "")
            return self.parent.error("http", args[0], res, code, "", {})
        elif action == "raise":
            raise urllib.error.URLError("blah")
        assert False