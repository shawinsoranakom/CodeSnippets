def __iter__(self):
        # Ticket #23721
        assert False, "type checking should happen without calling model __iter__"