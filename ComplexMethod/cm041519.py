def get_signature_kwargs(signing_algorithm, message_type):
    algo_map = {
        "SHA_256": (hashes.SHA256(), 32),
        "SHA_384": (hashes.SHA384(), 48),
        "SHA_512": (hashes.SHA512(), 64),
    }
    hasher, salt = next((h, s) for k, (h, s) in algo_map.items() if k in signing_algorithm)
    algorithm = utils.Prehashed(hasher) if message_type == "DIGEST" else hasher
    kwargs = {}

    if signing_algorithm.startswith("ECDSA"):
        kwargs["signature_algorithm"] = ec.ECDSA(algorithm)
    elif signing_algorithm.startswith("RSA"):
        if "PKCS" in signing_algorithm:
            kwargs["padding"] = padding.PKCS1v15()
        elif "PSS" in signing_algorithm:
            kwargs["padding"] = padding.PSS(mgf=padding.MGF1(hasher), salt_length=salt)
        kwargs["algorithm"] = algorithm
    return kwargs