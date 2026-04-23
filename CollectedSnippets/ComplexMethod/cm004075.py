def create_rename_keys(state_dict):
    rename_keys = []
    for k in state_dict:
        k_new = k
        if ".pwconv" in k:
            k_new = k_new.replace(".pwconv", ".point_wise_conv")
        if ".dwconv" in k:
            k_new = k_new.replace(".dwconv", ".depth_wise_conv")
        if ".Proj." in k:
            k_new = k_new.replace(".Proj.", ".proj.")
        if "patch_embed" in k_new:
            k_new = k_new.replace("patch_embed", "swiftformer.patch_embed.patch_embedding")
        if "network" in k_new:
            ls = k_new.split(".")
            if ls[2].isdigit():
                k_new = "swiftformer.encoder.network." + ls[1] + ".blocks." + ls[2] + "." + ".".join(ls[3:])
            else:
                k_new = k_new.replace("network", "swiftformer.encoder.network")
        rename_keys.append((k, k_new))
    return rename_keys