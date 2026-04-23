def fetch(self, fetcher, instance):
        instances = [
            peer
            for peer_weakref in instance._state.peers
            if (peer := peer_weakref()) is not None
        ]
        if len(instances) > 1:
            fetcher.fetch_many(instances)
        else:
            fetcher.fetch_one(instance)