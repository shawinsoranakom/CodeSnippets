def decode_chunk(chunk):
    # 提前读取一些信息（用于判断异常）
    chunk_decoded = chunk.decode()
    chunkjson = None
    is_last_chunk = False
    need_to_pass = False
    if chunk_decoded.startswith('data:'):
        try:
            chunkjson = json.loads(chunk_decoded[6:])
        except:
            need_to_pass = True
            pass
    elif chunk_decoded.startswith('event:'):
        try:
            event_type = chunk_decoded.split(':')[1].strip()
            if event_type == 'content_block_stop' or event_type == 'message_stop':
                is_last_chunk = True
            elif event_type == 'content_block_start' or event_type == 'message_start':
                need_to_pass = True
                pass
        except:
            need_to_pass = True
            pass
    else:
        need_to_pass = True
        pass
    return need_to_pass, chunkjson, is_last_chunk