def _num_seconds(self, dt):
        return int((dt - datetime(2001, 1, 1)).total_seconds())