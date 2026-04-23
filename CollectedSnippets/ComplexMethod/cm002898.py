def forward(ctx, query_mask, key_mask, query, key, value, config):
        if query_mask.size(0) != key_mask.size(0):
            raise ValueError("Query mask and Key mask differ in sizes in dimension 0")
        if query_mask.size(0) != query.size(0):
            raise ValueError("Query mask and Query differ in sizes in dimension 0")
        if query_mask.size(0) != key.size(0):
            raise ValueError("Query mask and Key differ in sizes in dimension 0")
        if query_mask.size(0) != value.size(0):
            raise ValueError("Query mask and Value mask differ in sizes in dimension 0")
        if key.size(1) != value.size(1):
            raise ValueError("Key and Value differ in sizes in dimension 1")
        if query.size(2) != key.size(2):
            raise ValueError("Query and Key differ in sizes in dimension 2")

        query_mask, key_mask, query, key, value = to_contiguous([query_mask, key_mask, query, key, value])

        use_cuda = query_mask.is_cuda
        num_hash = config["num_hash"]
        hash_code_len = config["hash_code_len"]
        hashtable_capacity = int(2**hash_code_len)

        if config["use_fast_hash"]:
            query_hash_code, key_hash_code = lsh_cumulation.fast_hash(
                query_mask, query, key_mask, key, num_hash, hash_code_len, use_cuda, 1
            )
        else:
            query_hash_code, key_hash_code = hashing(query, key, num_hash, hash_code_len)

        cumulation_value = lsh_cumulation.lsh_cumulation(
            query_mask, query_hash_code, key_mask, key_hash_code, value, hashtable_capacity, use_cuda, 1
        )

        ctx.save_for_backward(query_mask, key_mask, query_hash_code, key_hash_code, query, key, value)
        ctx.config = config

        return cumulation_value