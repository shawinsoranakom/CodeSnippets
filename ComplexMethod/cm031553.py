def add_handler(self, handler):
        if not hasattr(handler, "add_parent"):
            raise TypeError("expected BaseHandler instance, got %r" %
                            type(handler))

        added = False
        for meth in dir(handler):
            if meth in ["redirect_request", "do_open", "proxy_open"]:
                # oops, coincidental match
                continue

            i = meth.find("_")
            if i < 1:
                continue
            protocol = meth[:i]
            condition = meth[i+1:]

            if condition.startswith("error"):
                j = condition.find("_") + i + 1
                kind = meth[j+1:]
                try:
                    kind = int(kind)
                except ValueError:
                    pass
                lookup = self.handle_error.get(protocol, {})
                self.handle_error[protocol] = lookup
            elif condition == "open":
                kind = protocol
                lookup = self.handle_open
            elif condition == "response":
                kind = protocol
                lookup = self.process_response
            elif condition == "request":
                kind = protocol
                lookup = self.process_request
            else:
                continue

            handlers = lookup.setdefault(kind, [])
            if handlers:
                bisect.insort(handlers, handler)
            else:
                handlers.append(handler)
            added = True

        if added:
            bisect.insort(self.handlers, handler)
            handler.add_parent(self)