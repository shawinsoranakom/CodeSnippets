def proto_to_str(proto: Any) -> str:
    """Serializes a protobuf to a string (used here for hashing purposes)"""
    return proto.SerializePartialToString()