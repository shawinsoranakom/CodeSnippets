def sparsify_model(path_to_model, sparsified_model_dump_path):
    """Sparsifies the embedding layers of the dlrm model for different sparsity levels, norms and block shapes
    using the DataNormSparsifier.
    The function tracks the step time of the sparsifier and the size of the compressed checkpoint and collates
    it into a csv.

    Note::
        This function dumps a csv sparse_model_metadata.csv in the current directory.

    Args:
        path_to_model (str)
            path to the trained criteo model ckpt file
        sparsity_levels (List of float)
            list of sparsity levels to be sparsified on
        norms (List of str)
            list of norms to be sparsified on
        sparse_block_shapes (List of tuples)
            List of sparse block shapes to be sparsified on
    """
    sparsity_levels = [sl / 10 for sl in range(10)]
    sparsity_levels += [0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99, 1.0]

    norms = ["L1", "L2"]
    sparse_block_shapes = [(1, 1), (1, 4)]

    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")

    print("Running for sparsity levels - ", sparsity_levels)
    print("Running for sparse block shapes - ", sparse_block_shapes)
    print("Running for norms - ", norms)

    orig_model = get_dlrm_model()
    saved_state = torch.load(path_to_model, map_location=device)
    orig_model.load_state_dict(saved_state["state_dict"])

    orig_model = orig_model.to(device)
    step_time_dict = {}

    stat_dict: dict[str, list] = {
        "norm": [],
        "sparse_block_shape": [],
        "sparsity_level": [],
        "step_time_sec": [],
        "zip_file_size": [],
        "path": [],
    }
    for norm in norms:
        for sbs in sparse_block_shapes:
            if norm == "L2" and sbs == (1, 1):
                continue
            for sl in sparsity_levels:
                model = copy.deepcopy(orig_model)
                sparsifier = create_attach_sparsifier(
                    model, sparse_block_shape=sbs, norm=norm, sparsity_level=sl
                )

                t1 = time.time()
                sparsifier.step()
                t2 = time.time()

                step_time = t2 - t1
                norm_sl = f"{norm}_{sbs}_{sl}"
                print(f"Step Time for {norm_sl}=: {step_time} s")

                step_time_dict[norm_sl] = step_time

                sparsifier.squash_mask()

                saved_state["state_dict"] = model.state_dict()
                file_name = f"criteo_model_norm={norm}_sl={sl}.ckpt"
                state_path, file_size = save_model_states(
                    saved_state, sparsified_model_dump_path, file_name, sbs, norm=norm
                )

                stat_dict["norm"].append(norm)
                stat_dict["sparse_block_shape"].append(sbs)
                stat_dict["sparsity_level"].append(sl)
                stat_dict["step_time_sec"].append(step_time)
                stat_dict["zip_file_size"].append(file_size)
                stat_dict["path"].append(state_path)

    df = pd.DataFrame(stat_dict)
    filename = "sparse_model_metadata.csv"
    df.to_csv(filename, index=False)

    print(f"Saved sparsified metadata file in {filename}")