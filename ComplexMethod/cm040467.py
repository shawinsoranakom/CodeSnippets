def _parameterize_data(self, data, dynamic_batch_size=False):
        if isinstance(data, (list, tuple)):
            parametrize_data = []
            for elem in data:
                param_elem = self._parameterize_data(elem, dynamic_batch_size)
                parametrize_data.append(param_elem)
        elif isinstance(data, dict):
            parametrize_data = dict()
            for elem_name, elem in data.items():
                param_elem = self._parameterize_data(elem, dynamic_batch_size)
                parametrize_data[elem_name] = param_elem
        elif isinstance(data, OpenVINOKerasTensor):
            parametrize_data = data
        elif isinstance(data, np.ndarray) or np.isscalar(data):
            ov_type = OPENVINO_DTYPES[str(data.dtype)]
            ov_shape = list(data.shape)
            if dynamic_batch_size and len(ov_shape) > 0:
                ov_shape[0] = -1
            param = ov_opset.parameter(shape=ov_shape, dtype=ov_type)
            parametrize_data = OpenVINOKerasTensor(param.output(0))
        elif isinstance(data, int):
            param = ov_opset.parameter(shape=[], dtype=ov.Type.i32)
            parametrize_data = OpenVINOKerasTensor(param.output(0))
        elif isinstance(data, float):
            param = ov_opset.parameter(shape=[], dtype=ov.Type.f32)
            parametrize_data = OpenVINOKerasTensor(param.output(0))
        else:
            raise ValueError(f"Unknown type of input data {type(data)}")
        return parametrize_data