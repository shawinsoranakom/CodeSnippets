def _really_load(self, f, filename, ignore_discard, ignore_expires):
        now = time.time()

        if not NETSCAPE_MAGIC_RGX.match(f.readline()):
            raise LoadError(
                "%r does not look like a Netscape format cookies file" %
                filename)

        try:
            while (line := f.readline()) != "":
                rest = {}

                # httponly is a cookie flag as defined in rfc6265
                # when encoded in a netscape cookie file,
                # the line is prepended with "#HttpOnly_"
                if line.startswith(HTTPONLY_PREFIX):
                    rest[HTTPONLY_ATTR] = ""
                    line = line[len(HTTPONLY_PREFIX):]

                # last field may be absent, so keep any trailing tab
                if line.endswith("\n"): line = line[:-1]

                # skip comments and blank lines XXX what is $ for?
                if (line.strip().startswith(("#", "$")) or
                    line.strip() == ""):
                    continue

                domain, domain_specified, path, secure, expires, name, value = \
                        line.split("\t")
                secure = (secure == "TRUE")
                domain_specified = (domain_specified == "TRUE")
                if name == "":
                    # cookies.txt regards 'Set-Cookie: foo' as a cookie
                    # with no name, whereas http.cookiejar regards it as a
                    # cookie with no value.
                    name = value
                    value = None

                initial_dot = domain.startswith(".")
                assert domain_specified == initial_dot

                discard = False
                if expires == "":
                    expires = None
                    discard = True

                # assume path_specified is false
                c = Cookie(0, name, value,
                           None, False,
                           domain, domain_specified, initial_dot,
                           path, False,
                           secure,
                           expires,
                           discard,
                           None,
                           None,
                           rest)
                if not ignore_discard and c.discard:
                    continue
                if not ignore_expires and c.is_expired(now):
                    continue
                self.set_cookie(c)

        except OSError:
            raise
        except Exception:
            _warn_unhandled_exception()
            raise LoadError("invalid Netscape format cookies file %r: %r" %
                            (filename, line))