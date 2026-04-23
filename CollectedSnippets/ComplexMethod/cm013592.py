def _tensor_meta_to_label(self, tm: object) -> str:
            if tm is None:
                return ""
            elif isinstance(tm, TensorMetadata):
                return self._stringify_tensor_meta(tm)
            elif isinstance(tm, list):
                result = ""
                for item in tm:
                    result += self._tensor_meta_to_label(item)
                return result
            elif isinstance(tm, dict):
                result = ""
                for v in tm.values():
                    result += self._tensor_meta_to_label(v)
                return result
            elif isinstance(tm, tuple):
                result = ""
                for item in tm:
                    result += self._tensor_meta_to_label(item)
                return result
            else:
                raise RuntimeError(f"Unsupported tensor meta type {type(tm)}")