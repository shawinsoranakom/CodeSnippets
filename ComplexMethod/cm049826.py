def _broadcast(self, /, *, delete=False):
        for canned_response in self:
            stores = [Store(bus_channel=group) for group in canned_response.group_ids]
            for user in self.env.user | canned_response.create_uid:
                if not user.all_group_ids & canned_response.group_ids:
                    stores.append(Store(bus_channel=user))
            for store in stores:
                if delete:
                    store.delete(canned_response)
                else:
                    store.add(canned_response)
            for store in stores:
                store.bus_send()