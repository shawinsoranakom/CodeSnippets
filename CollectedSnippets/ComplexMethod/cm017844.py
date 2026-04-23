def get_traceback_data(self):
        """Return a dictionary containing traceback information."""
        if self.exc_type and issubclass(self.exc_type, TemplateDoesNotExist):
            self.template_does_not_exist = True
            self.postmortem = self.exc_value.chain or [self.exc_value]

        frames = self.get_traceback_frames()
        for i, frame in enumerate(frames):
            if "vars" in frame:
                frame_vars = []
                for k, v in frame["vars"]:
                    v = pprint(v)
                    # Trim large blobs of data
                    if len(v) > 4096:
                        v = "%s… <trimmed %d bytes string>" % (v[0:4096], len(v))
                    frame_vars.append((k, v))
                frame["vars"] = frame_vars
            frames[i] = frame

        unicode_hint = ""
        if self.exc_type and issubclass(self.exc_type, UnicodeError):
            start = getattr(self.exc_value, "start", None)
            end = getattr(self.exc_value, "end", None)
            if start is not None and end is not None:
                unicode_str = self.exc_value.args[1]
                unicode_hint = force_str(
                    unicode_str[max(start - 5, 0) : min(end + 5, len(unicode_str))],
                    "ascii",
                    errors="replace",
                )
        from django import get_version

        if self.request is None:
            user_str = None
        else:
            try:
                user_str = str(self.request.user)
            except Exception:
                # request.user may raise OperationalError if the database is
                # unavailable, for example.
                user_str = "[unable to retrieve the current user]"

        c = {
            "is_email": self.is_email,
            "unicode_hint": unicode_hint,
            "frames": frames,
            "request": self.request,
            "request_meta": self.filter.get_safe_request_meta(self.request),
            "request_COOKIES_items": self.filter.get_safe_cookies(self.request).items(),
            "user_str": user_str,
            "filtered_POST_items": list(
                self.filter.get_post_parameters(self.request).items()
            ),
            "settings": self.filter.get_safe_settings(),
            "sys_executable": sys.executable,
            "sys_version_info": "%d.%d.%d" % sys.version_info[0:3],
            "server_time": timezone.now(),
            "django_version_info": get_version(),
            "sys_path": sys.path,
            "template_info": self.template_info,
            "template_does_not_exist": self.template_does_not_exist,
            "postmortem": self.postmortem,
        }
        if self.request is not None:
            c["request_GET_items"] = self.request.GET.items()
            c["request_FILES_items"] = self.request.FILES.items()
            c["request_insecure_uri"] = self._get_raw_insecure_uri()
            c["raising_view_name"] = get_caller(self.request)

        # Check whether exception info is available
        if self.exc_type:
            c["exception_type"] = self.exc_type.__name__
        if self.exc_value:
            c["exception_value"] = getattr(
                self.exc_value, "raw_error_message", self.exc_value
            )
            if exc_notes := getattr(self.exc_value, "__notes__", None):
                c["exception_notes"] = "\n" + "\n".join(exc_notes)
        if frames:
            c["lastframe"] = frames[-1]
        return c