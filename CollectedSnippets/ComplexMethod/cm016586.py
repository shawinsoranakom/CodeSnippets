def state_dict(self, *args, destination=None, prefix="", **kwargs):
                if destination is not None:
                    sd = destination
                else:
                    sd = {}

                if not hasattr(self, 'weight'):
                    logging.warning("Warning: state dict on uninitialized op {}".format(prefix))
                    return sd

                if self.bias is not None:
                    sd["{}bias".format(prefix)] = self.bias

                if self.weight is None:
                    return sd

                if isinstance(self.weight, QuantizedTensor):
                    sd_out = self.weight.state_dict("{}weight".format(prefix))
                    for k in sd_out:
                        sd[k] = sd_out[k]

                    quant_conf = {"format": self.quant_format}
                    if self._full_precision_mm_config:
                        quant_conf["full_precision_matrix_mult"] = True
                    sd["{}comfy_quant".format(prefix)] = torch.tensor(list(json.dumps(quant_conf).encode('utf-8')), dtype=torch.uint8)

                    input_scale = getattr(self, 'input_scale', None)
                    if input_scale is not None:
                        sd["{}input_scale".format(prefix)] = input_scale
                else:
                    sd["{}weight".format(prefix)] = self.weight
                return sd