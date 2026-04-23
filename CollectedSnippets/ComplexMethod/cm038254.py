def _prepare_multimodal_kwargs(self, **kwargs: object):
        output = defaultdict(list)
        for k, v in kwargs.items():
            if len(v) < 1 or len(v[0]) < 1:
                continue  # if empty batch of empty sample

            new_k, is_video = k, False
            if not k.endswith("_images") and not k.endswith("_videos"):
                pass
            else:
                new_k, is_video = k.split("_")[:-1], k.split("_")[-1]
                new_k = "_".join(new_k)
                is_video = is_video == "videos"

            for _sample_idx, _v in enumerate(v):  # batch -> sample
                if new_k not in ["pixel_values"]:
                    if len(output[new_k]) < _sample_idx + 1:
                        output[new_k].append(list())
                    _v = _v.detach().cpu().numpy().tolist()
                    output[new_k][_sample_idx] += _v
                elif isinstance(_v, torch.Tensor):
                    if len(output[new_k]) < _sample_idx + 1:
                        output[new_k].append(list())
                        output["is_videos"].append(list())
                    _v = list(torch.unbind(_v, dim=0))
                    output[new_k][_sample_idx] += _v
                    output["is_videos"][_sample_idx] += [
                        is_video,
                    ] * len(_v)
        return dict(output)