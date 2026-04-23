def create_embedding_from_data(data, name, filename='unknown embedding file', filepath=None):
    if 'string_to_param' in data:  # textual inversion embeddings
        param_dict = data['string_to_param']
        param_dict = getattr(param_dict, '_parameters', param_dict)  # fix for torch 1.12.1 loading saved file from torch 1.11
        assert len(param_dict) == 1, 'embedding file has multiple terms in it'
        emb = next(iter(param_dict.items()))[1]
        vec = emb.detach().to(devices.device, dtype=torch.float32)
        shape = vec.shape[-1]
        vectors = vec.shape[0]
    elif type(data) == dict and 'clip_g' in data and 'clip_l' in data:  # SDXL embedding
        vec = {k: v.detach().to(devices.device, dtype=torch.float32) for k, v in data.items()}
        shape = data['clip_g'].shape[-1] + data['clip_l'].shape[-1]
        vectors = data['clip_g'].shape[0]
    elif type(data) == dict and type(next(iter(data.values()))) == torch.Tensor:  # diffuser concepts
        assert len(data.keys()) == 1, 'embedding file has multiple terms in it'

        emb = next(iter(data.values()))
        if len(emb.shape) == 1:
            emb = emb.unsqueeze(0)
        vec = emb.detach().to(devices.device, dtype=torch.float32)
        shape = vec.shape[-1]
        vectors = vec.shape[0]
    else:
        raise Exception(f"Couldn't identify {filename} as neither textual inversion embedding nor diffuser concept.")

    embedding = Embedding(vec, name)
    embedding.step = data.get('step', None)
    embedding.sd_checkpoint = data.get('sd_checkpoint', None)
    embedding.sd_checkpoint_name = data.get('sd_checkpoint_name', None)
    embedding.vectors = vectors
    embedding.shape = shape

    if filepath:
        embedding.filename = filepath
        embedding.set_hash(hashes.sha256(filepath, "textual_inversion/" + name) or '')

    return embedding