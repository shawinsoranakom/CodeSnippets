def get_lookup(self, lookup_name):
        self.call_order.append("lookup")
        return super().get_lookup(lookup_name)