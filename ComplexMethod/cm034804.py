def stream_chunks(bucket_dir: Path, delete_files: bool = False, refine_chunks_with_spacy: bool = False, event_stream: bool = False) -> Iterator[str]:
    size = 0
    if refine_chunks_with_spacy:
        for chunk in stream_read_parts_and_refine(bucket_dir, delete_files):
            if event_stream:
                size += len(chunk.encode())
                yield f'data: {json.dumps({"action": "refine", "size": size})}\n\n'
            else:
                yield chunk
    else:
        streaming = stream_read_files(bucket_dir, get_filenames(bucket_dir), delete_files)
        streaming = cache_stream(streaming, bucket_dir)
        for chunk in streaming:
            if event_stream:
                size += len(chunk.encode())
                yield f'data: {json.dumps({"action": "load", "size": size})}\n\n'
            else:
                yield chunk
        files_txt = os.path.join(bucket_dir, FILE_LIST)
        if os.path.exists(files_txt):
            for filename in get_filenames(bucket_dir):
                if is_allowed_extension(filename):
                    yield f'data: {json.dumps({"action": "media", "filename": filename})}\n\n'
                if delete_files and os.path.exists(os.path.join(bucket_dir, filename)):
                    os.remove(os.path.join(bucket_dir, filename))
            os.remove(files_txt)
            if event_stream:
                yield f'data: {json.dumps({"action": "delete_files"})}\n\n'
    if event_stream:
        yield f'data: {json.dumps({"action": "done", "size": size})}\n\n'