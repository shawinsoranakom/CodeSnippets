def equalAndThen(self, x, y, msg, k):
        """
        Helper for implementing "requireEqual" and "checkEqual".  Upon failure,
        invokes continuation "k" with the error message.
        """
        if isinstance(x, onnx.TensorProto) and isinstance(y, onnx.TensorProto):
            self.equalAndThen(x.name, y.name, msg, k)
            # Use numpy for the comparison
            t1 = onnx.numpy_helper.to_array(x)
            t2 = onnx.numpy_helper.to_array(y)
            new_msg = f"{colonize(msg)}In embedded parameter '{x.name}'"
            self.equalAndThen(t1, t2, new_msg, k)
        elif isinstance(x, np.ndarray) and isinstance(y, np.ndarray):
            np.testing.assert_equal(x, y)
        else:
            if x != y:
                # TODO: Better algorithm for lists
                sx = str(x)
                sy = str(y)
                if len(sx) > 40 or len(sy) > 40 or "\n" in sx or "\n" in sy:
                    # long form
                    l = "=" * 50
                    k(
                        "\n{}The value\n{}\n{}\n{}\n\ndoes not equal\n\n{}\n{}\n{}".format(
                            colonize(msg, ":\n"), l, sx, l, l, sy, l
                        )
                    )
                else:
                    k(f"{colonize(msg)}{sx} != {sy}")