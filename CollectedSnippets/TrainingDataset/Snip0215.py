def base16_encode(data: bytes) -> str:
   
    return "".join([hex(byte)[2:].zfill(2).upper() for byte in list(data)])
