def _exec_jsonrpc(self, name, *args, **kwargs):

        req = request_builder(name, *args, **kwargs)
        reqid = req['id']

        if not os.path.exists(self.socket_path):
            raise ConnectionError(
                'socket path %s does not exist or cannot be found. See Troubleshooting socket '
                'path issues in the Network Debug and Troubleshooting Guide' % self.socket_path
            )

        try:
            data = json.dumps(req, cls=_get_legacy_encoder(), vault_to_text=True)
        except TypeError as exc:
            raise ConnectionError(
                "Failed to encode some variables as JSON for communication with the persistent connection helper. "
                "The original exception was: %s" % to_text(exc)
            )

        try:
            out = self.send(data)
        except OSError as ex:
            raise ConnectionError(
                f'Unable to connect to socket {self.socket_path!r}. See Troubleshooting socket path issues '
                'in the Network Debug and Troubleshooting Guide.'
            ) from ex

        try:
            response = json.loads(out)
        except ValueError:
            # set_option(s) has sensitive info, and the details are unlikely to matter anyway
            if name.startswith("set_option"):
                raise ConnectionError(
                    "Unable to decode JSON from response to {0}. Received '{1}'.".format(name, out)
                )
            params = [repr(arg) for arg in args] + ['{0}={1!r}'.format(k, v) for k, v in kwargs.items()]
            params = ', '.join(params)
            raise ConnectionError(
                "Unable to decode JSON from response to {0}({1}). Received '{2}'.".format(name, params, out)
            )

        if response['id'] != reqid:
            raise ConnectionError('invalid json-rpc id received')
        if "result_type" in response:
            # NOTE: while pickle.loads is normally a concern, in this case it is controller code on the same
            # machine and user in a private restricted path, any substitution would require same privs.
            response["result"] = pickle.loads(to_bytes(response["result"], errors="surrogateescape"))

        return response