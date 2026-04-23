def _handle_request(self, c):
        request = None
        try:
            connection.deliver_challenge(c, self.authkey)
            connection.answer_challenge(c, self.authkey)
            request = c.recv()
            ignore, funcname, args, kwds = request
            assert funcname in self.public, '%r unrecognized' % funcname
            func = getattr(self, funcname)
        except Exception:
            msg = ('#TRACEBACK', format_exc())
        else:
            try:
                result = func(c, *args, **kwds)
            except Exception:
                msg = ('#TRACEBACK', format_exc())
            else:
                msg = ('#RETURN', result)

        try:
            c.send(msg)
        except Exception as e:
            try:
                c.send(('#TRACEBACK', format_exc()))
            except Exception:
                pass
            util.info('Failure to send message: %r', msg)
            util.info(' ... request was %r', request)
            util.info(' ... exception was %r', e)