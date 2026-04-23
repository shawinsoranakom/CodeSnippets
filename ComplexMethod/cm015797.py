def compare_dict_tensors(self, ref_dict, res_dict, rtol=1e-3, atol=1e-3):
        if len(set(ref_dict.keys())) != len(set(res_dict.keys())):
            return False
        for key1 in ref_dict:
            key2 = "_orig_mod." + key1
            if key2 not in res_dict:
                raise AssertionError(f"{key1} does not exist in traced module")
            # if both of them are None, continue
            if (
                not isinstance(ref_dict[key1], torch.Tensor)
                and not isinstance(res_dict[key2], torch.Tensor)
                and ref_dict[key1] is None
                and res_dict[key2] is None
            ):
                log.info(
                    "None found with key1 and value 1: %s, %s, key2 and value2 %s, %s",
                    key1,
                    ref_dict[key1],
                    key2,
                    res_dict[key2],
                )
                continue
            elif not torch.allclose(
                ref_dict[key1], res_dict[key2], rtol=rtol, atol=atol, equal_nan=True
            ):
                log.info(
                    "gradient mismatch for eager and compiled modules, with eager: %s and compiled: %s",
                    ref_dict[key1],
                    res_dict[key2],
                )
                return False
        return True