def fn(x):
            a = 0
            if x.is_replicate():
                a += 1
            if x.is_shard():
                a += 2
                if x.dim < 0:
                    raise RuntimeError("dim < 0")
            if x.is_shard(0):
                a += 2
            if x.is_shard(dim=0):
                a += 2
            if x.is_shard(dim=None):
                a += 2
            if x.is_partial():
                a += 3
            return a