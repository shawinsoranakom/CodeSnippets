def address_string(self):
        # Short-circuit parent method to not call socket.getfqdn
        return self.client_address[0]