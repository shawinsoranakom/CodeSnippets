def create_embedding(name, num_vectors_per_token, overwrite_old, init_text='*'):
    cond_model = shared.sd_model.cond_stage_model

    with devices.autocast():
        cond_model([""])  # will send cond model to GPU if lowvram/medvram is active

    #cond_model expects at least some text, so we provide '*' as backup.
    embedded = cond_model.encode_embedding_init_text(init_text or '*', num_vectors_per_token)
    vec = torch.zeros((num_vectors_per_token, embedded.shape[1]), device=devices.device)

    #Only copy if we provided an init_text, otherwise keep vectors as zeros
    if init_text:
        for i in range(num_vectors_per_token):
            vec[i] = embedded[i * int(embedded.shape[0]) // num_vectors_per_token]

    # Remove illegal characters from name.
    name = "".join( x for x in name if (x.isalnum() or x in "._- "))
    fn = os.path.join(shared.cmd_opts.embeddings_dir, f"{name}.pt")
    if not overwrite_old:
        assert not os.path.exists(fn), f"file {fn} already exists"

    embedding = Embedding(vec, name)
    embedding.step = 0
    embedding.save(fn)

    return fn