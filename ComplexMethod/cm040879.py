def validate_sse_c(
    algorithm: SSECustomerAlgorithm,
    encryption_key: SSECustomerKey,
    encryption_key_md5: SSECustomerKeyMD5,
    server_side_encryption: ServerSideEncryption = None,
):
    """
    This method validates the SSE Customer parameters for different requests.
    :param algorithm: the SSECustomerAlgorithm parameter of the incoming Request, can only be AES256
    :param encryption_key: the SSECustomerKey of the incoming Request, represent the base64 encoded encryption key
    :param encryption_key_md5: the SSECustomerKeyMD5 of the request, represents the base64 encoded MD5 hash of the
    encryption key
    :param server_side_encryption: when the incoming request is a "write" request (PutObject, CopyObject,
     CreateMultipartUpload), the user can specify the encryption. Customer encryption and AWS SSE can't both be set.
    :raises: InvalidArgument if the request is invalid
    :raises: InvalidEncryptionAlgorithmError if the given algorithm is different from AES256
    """
    if not encryption_key and not algorithm:
        return
    elif server_side_encryption:
        raise InvalidArgument(
            "Server Side Encryption with Customer provided key is incompatible with the encryption method specified",
            ArgumentName="x-amz-server-side-encryption",
            ArgumentValue=server_side_encryption,
        )

    if encryption_key and not algorithm:
        raise InvalidArgument(
            "Requests specifying Server Side Encryption with Customer provided keys must provide a valid encryption algorithm.",
            ArgumentName="x-amz-server-side-encryption",
        )
    elif not encryption_key and algorithm:
        raise InvalidArgument(
            "Requests specifying Server Side Encryption with Customer provided keys must provide an appropriate secret key.",
            ArgumentName="x-amz-server-side-encryption",
        )

    if algorithm != "AES256":
        raise InvalidEncryptionAlgorithmError(
            "The Encryption request you specified is not valid. Supported value: AES256.",
            ArgumentName="x-amz-server-side-encryption",
            ArgumentValue=algorithm,
        )

    sse_customer_key = base64.b64decode(encryption_key)
    if len(sse_customer_key) != 32:
        raise InvalidArgument(
            "The secret key was invalid for the specified algorithm.",
            ArgumentName="x-amz-server-side-encryption",
        )

    sse_customer_key_md5 = base64.b64encode(hashlib.md5(sse_customer_key).digest()).decode("utf-8")
    if sse_customer_key_md5 != encryption_key_md5:
        raise InvalidArgument(
            "The calculated MD5 hash of the key did not match the hash that was provided.",
            # weirdly, the argument name is wrong, it should be `x-amz-server-side-encryption-customer-key-MD5`
            ArgumentName="x-amz-server-side-encryption",
        )