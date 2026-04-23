def json(k: str, v: object) -> object:
            # Some best-effort debugging serialization for unserializable
            # fields (feel free to add other special cases as appropriate)
            if k in ["data", "autograd_meta_from"]:
                return None  # never repr these
            if k in MetaTensorDesc._UNSERIALIZABLE:
                return repr(v)
            if isinstance(v, (torch.device, torch.dtype, torch.layout)):
                return repr(v)
            if isinstance(v, torch.SymInt):
                return repr(v)
            if isinstance(v, (tuple, list)):
                return [json(k, v1) for v1 in v]
            if isinstance(v, (MetaStorageDesc, MetaTensorDesc)):
                return v.id
            if isinstance(v, CreationMeta):
                return str(v)
            if k == "attrs" and isinstance(v, dict):
                return {k1: v1.id for k1, v1 in v.items()}
            return v