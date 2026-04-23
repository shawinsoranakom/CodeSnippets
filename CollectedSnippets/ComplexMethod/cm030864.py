def __init__(self, certificate=None, ssl_version=None,
                 certreqs=None, cacerts=None,
                 chatty=True, connectionchatty=False, starttls_server=False,
                 alpn_protocols=None,
                 ciphers=None, context=None):
        if context:
            self.context = context
        else:
            self.context = ssl.SSLContext(ssl_version
                                          if ssl_version is not None
                                          else ssl.PROTOCOL_TLS_SERVER)
            self.context.verify_mode = (certreqs if certreqs is not None
                                        else ssl.CERT_NONE)
            if cacerts:
                self.context.load_verify_locations(cacerts)
            if certificate:
                self.context.load_cert_chain(certificate)
            if alpn_protocols:
                self.context.set_alpn_protocols(alpn_protocols)
            if ciphers:
                self.context.set_ciphers(ciphers)
        self.chatty = chatty
        self.connectionchatty = connectionchatty
        self.starttls_server = starttls_server
        self.sock = socket.socket()
        self.port = socket_helper.bind_port(self.sock)
        self.flag = None
        self.active = False
        self.selected_alpn_protocols = []
        self.shared_ciphers = []
        self.conn_errors = []
        threading.Thread.__init__(self)
        self.daemon = True
        self._in_context = False