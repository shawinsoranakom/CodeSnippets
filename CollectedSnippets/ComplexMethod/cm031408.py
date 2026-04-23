def _really_load(self, f, filename, ignore_discard, ignore_expires):
        magic = f.readline()
        if not self.magic_re.search(magic):
            msg = ("%r does not look like a Set-Cookie3 (LWP) format "
                   "file" % filename)
            raise LoadError(msg)

        now = time.time()

        header = "Set-Cookie3:"
        boolean_attrs = ("port_spec", "path_spec", "domain_dot",
                         "secure", "discard")
        value_attrs = ("version",
                       "port", "path", "domain",
                       "expires",
                       "comment", "commenturl")

        try:
            while (line := f.readline()) != "":
                if not line.startswith(header):
                    continue
                line = line[len(header):].strip()

                for data in split_header_words([line]):
                    name, value = data[0]
                    standard = {}
                    rest = {}
                    for k in boolean_attrs:
                        standard[k] = False
                    for k, v in data[1:]:
                        if k is not None:
                            lc = k.lower()
                        else:
                            lc = None
                        # don't lose case distinction for unknown fields
                        if (lc in value_attrs) or (lc in boolean_attrs):
                            k = lc
                        if k in boolean_attrs:
                            if v is None: v = True
                            standard[k] = v
                        elif k in value_attrs:
                            standard[k] = v
                        else:
                            rest[k] = v

                    h = standard.get
                    expires = h("expires")
                    discard = h("discard")
                    if expires is not None:
                        expires = iso2time(expires)
                    if expires is None:
                        discard = True
                    domain = h("domain")
                    domain_specified = domain.startswith(".")
                    c = Cookie(h("version"), name, value,
                               h("port"), h("port_spec"),
                               domain, domain_specified, h("domain_dot"),
                               h("path"), h("path_spec"),
                               h("secure"),
                               expires,
                               discard,
                               h("comment"),
                               h("commenturl"),
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
            raise LoadError("invalid Set-Cookie3 format file %r: %r" %
                            (filename, line))