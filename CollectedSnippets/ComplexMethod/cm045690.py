def _hash_to_output(hash_val, *, format):
    if format == "hash":
        return hash_val
    elif format == "hex":
        return hash_val.hexdigest()
    elif format == "token":
        return hash_val.hexdigest()[-16:]
    elif format == "short_token":
        return hash_val.hexdigest()[-8:]
    elif format == "bytes":
        return hash_val.digest()
    elif format == "bignum":
        return int(hash_val.hexdigest(), 16)
    elif format == "u64":
        return int(hash_val.hexdigest(), 16) % (2**64)
    elif format == "i64":
        return int(hash_val.hexdigest(), 16) % (2**64) - (2**63)
    elif format == "bigint":
        return int(hash_val.hexdigest(), 16) % (2**63)
    elif format == "u32":
        return int(hash_val.hexdigest(), 16) % (2**32)
    elif format == "i32":
        return int(hash_val.hexdigest(), 16) % (2**32) - (2**31)
    elif format == "integer":
        return int(hash_val.hexdigest(), 16) % (2**31)
    elif format == "u16":
        return int(hash_val.hexdigest(), 16) % (2**16)
    elif format == "i16":
        return int(hash_val.hexdigest(), 16) % (2**16) - (2**15)
    else:
        raise NotImplementedError()