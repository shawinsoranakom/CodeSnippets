def profile_onnx_model(self, onnx_file: str, eps: float = 1e-3):
        """Profile an ONNX model, measuring average inference time and standard deviation across multiple runs.

        Args:
            onnx_file (str): Path to the ONNX model file.
            eps (float): Small epsilon value to prevent division by zero.

        Returns:
            (tuple[float, float]): Mean and standard deviation of inference time in milliseconds.
        """
        check_requirements([("onnxruntime", "onnxruntime-gpu")])  # either package meets requirements
        import onnxruntime as ort

        # Session with either 'TensorrtExecutionProvider', 'CUDAExecutionProvider', 'CPUExecutionProvider'
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        sess_options.intra_op_num_threads = 8  # Limit the number of threads
        sess = ort.InferenceSession(onnx_file, sess_options, providers=["CPUExecutionProvider"])

        input_data_dict = {}
        for input_tensor in sess.get_inputs():
            input_type = input_tensor.type
            if self.check_dynamic(input_tensor.shape):
                if len(input_tensor.shape) != 4 and self.check_dynamic(input_tensor.shape[1:]):
                    raise ValueError(f"Unsupported dynamic shape {input_tensor.shape} of {input_tensor.name}")
                input_shape = (
                    (1, 3, self.imgsz, self.imgsz) if len(input_tensor.shape) == 4 else (1, *input_tensor.shape[1:])
                )
            else:
                input_shape = input_tensor.shape

            # Mapping ONNX datatype to numpy datatype
            if "float16" in input_type:
                input_dtype = np.float16
            elif "float" in input_type:
                input_dtype = np.float32
            elif "double" in input_type:
                input_dtype = np.float64
            elif "int64" in input_type:
                input_dtype = np.int64
            elif "int32" in input_type:
                input_dtype = np.int32
            else:
                raise ValueError(f"Unsupported ONNX datatype {input_type}")

            input_data = np.random.rand(*input_shape).astype(input_dtype)
            input_name = input_tensor.name
            input_data_dict[input_name] = input_data

        output_name = sess.get_outputs()[0].name

        # Warmup runs
        elapsed = 0.0
        for _ in range(3):
            start_time = time.time()
            for _ in range(self.num_warmup_runs):
                sess.run([output_name], input_data_dict)
            elapsed = time.time() - start_time

        # Compute number of runs as higher of min_time or num_timed_runs
        num_runs = max(round(self.min_time / (elapsed + eps) * self.num_warmup_runs), self.num_timed_runs)

        # Timed runs
        run_times = []
        for _ in TQDM(range(num_runs), desc=onnx_file):
            start_time = time.time()
            sess.run([output_name], input_data_dict)
            run_times.append((time.time() - start_time) * 1000)  # Convert to milliseconds

        run_times = self.iterative_sigma_clipping(np.array(run_times), sigma=2, max_iters=5)  # sigma clipping
        return np.mean(run_times), np.std(run_times)