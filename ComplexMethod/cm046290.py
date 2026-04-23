def load_model(self, weight: str | Path) -> None:
        """Load a Google TensorFlow model in SavedModel, GraphDef, TFLite, or Edge TPU format.

        Args:
            weight (str | Path): Path to the model file or directory.
        """
        if self.format in {"saved_model", "pb"}:
            import tensorflow as tf

        if self.format == "saved_model":
            LOGGER.info(f"Loading {weight} for TensorFlow SavedModel inference...")
            self.model = tf.saved_model.load(weight)
            # Load metadata
            metadata_file = Path(weight) / "metadata.yaml"
            if metadata_file.exists():
                from ultralytics.utils import YAML

                self.apply_metadata(YAML.load(metadata_file))
        elif self.format == "pb":
            LOGGER.info(f"Loading {weight} for TensorFlow GraphDef inference...")
            from ultralytics.utils.export.tensorflow import gd_outputs

            def wrap_frozen_graph(gd, inputs, outputs):
                """Wrap a TensorFlow frozen graph for inference by pruning to specified input/output nodes."""
                x = tf.compat.v1.wrap_function(lambda: tf.compat.v1.import_graph_def(gd, name=""), [])
                ge = x.graph.as_graph_element
                return x.prune(tf.nest.map_structure(ge, inputs), tf.nest.map_structure(ge, outputs))

            gd = tf.Graph().as_graph_def()
            with open(weight, "rb") as f:
                gd.ParseFromString(f.read())
            self.frozen_func = wrap_frozen_graph(gd, inputs="x:0", outputs=gd_outputs(gd))

            # Try to find metadata
            try:
                metadata_file = next(
                    Path(weight).resolve().parent.rglob(f"{Path(weight).stem}_saved_model*/metadata.yaml")
                )
                from ultralytics.utils import YAML

                self.apply_metadata(YAML.load(metadata_file))
            except StopIteration:
                pass
        else:  # tflite and edgetpu
            try:
                from tflite_runtime.interpreter import Interpreter, load_delegate

                self.tf = None
            except ImportError:
                import tensorflow as tf

                self.tf = tf
                Interpreter, load_delegate = tf.lite.Interpreter, tf.lite.experimental.load_delegate

            if self.format == "edgetpu":
                device = self.device[3:] if str(self.device).startswith("tpu") else ":0"
                LOGGER.info(f"Loading {weight} on device {device[1:]} for TensorFlow Lite Edge TPU inference...")
                delegate = {"Linux": "libedgetpu.so.1", "Darwin": "libedgetpu.1.dylib", "Windows": "edgetpu.dll"}[
                    platform.system()
                ]
                self.interpreter = Interpreter(
                    model_path=str(weight),
                    experimental_delegates=[load_delegate(delegate, options={"device": device})],
                )
                self.device = torch.device("cpu")  # Edge TPU runs on CPU from PyTorch's perspective
            else:
                LOGGER.info(f"Loading {weight} for TensorFlow Lite inference...")
                self.interpreter = Interpreter(model_path=weight)

            self.interpreter.allocate_tensors()
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()

            # Load metadata
            try:
                with zipfile.ZipFile(weight, "r") as zf:
                    name = zf.namelist()[0]
                    contents = zf.read(name).decode("utf-8")
                    if name == "metadata.json":
                        self.apply_metadata(json.loads(contents))
                    else:
                        self.apply_metadata(ast.literal_eval(contents))
            except (zipfile.BadZipFile, SyntaxError, ValueError, json.JSONDecodeError):
                pass