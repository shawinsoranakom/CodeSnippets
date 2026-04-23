def chunk_block(cls, block_txt_list, chunk_token_num=512):
        chunks = []
        current_block = ""
        current_token_count = 0

        for block in block_txt_list:
            tks_str = rag_tokenizer.tokenize(block)
            block_token_count = len(tks_str.split(" ")) if tks_str else 0
            if block_token_count > chunk_token_num:
                if current_block:
                    chunks.append(current_block)
                start = 0
                tokens = tks_str.split(" ")
                while start < len(tokens):
                    end = start + chunk_token_num
                    split_tokens = tokens[start:end]
                    chunks.append(" ".join(split_tokens))
                    start = end
                current_block = ""
                current_token_count = 0
            else:
                if current_token_count + block_token_count <= chunk_token_num:
                    current_block += ("\n" if current_block else "") + block
                    current_token_count += block_token_count
                else:
                    chunks.append(current_block)
                    current_block = block
                    current_token_count = block_token_count

        if current_block:
            chunks.append(current_block)

        return chunks