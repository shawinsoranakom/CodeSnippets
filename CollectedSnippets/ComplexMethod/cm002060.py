def test_empty_input_string(self):
        tokenizer_return_type = []
        output_tensor_type = []

        if is_torch_available():
            import numpy as np
            import torch

            tokenizer_return_type.append("pt")
            output_tensor_type.append(torch.int64)
            tokenizer_return_type.append("np")
            output_tensor_type.append(np.int64)

        if is_mlx_available():
            import mlx.core as mx

            tokenizer_return_type.append("mlx")
            output_tensor_type.append(mx.int32)

        if len(tokenizer_return_type) == 0:
            self.skipTest(reason="No expected framework from PT, or MLX found")

        tokenizers = self.get_tokenizers()
        for tokenizer in tokenizers:
            with self.subTest(f"{tokenizer.__class__.__name__}"):
                nodes, xpaths = self.get_empty_nodes_and_xpaths()
                for return_type, target_type in zip(tokenizer_return_type, output_tensor_type):
                    output = tokenizer(nodes, xpaths=xpaths, return_tensors=return_type)
                    self.assertEqual(output.input_ids.dtype, target_type)

                question, nodes, xpaths = self.get_empty_question_nodes_and_xpaths()
                for return_type, target_type in zip(tokenizer_return_type, output_tensor_type):
                    output = tokenizer(nodes, xpaths=xpaths, return_tensors=return_type)
                    self.assertEqual(output.input_ids.dtype, target_type)

                nodes, xpaths = self.get_empty_nodes_and_xpaths_batch()
                for return_type, target_type in zip(tokenizer_return_type, output_tensor_type):
                    output = tokenizer(nodes, xpaths=xpaths, padding=True, return_tensors=return_type)
                    self.assertEqual(output.input_ids.dtype, target_type)

                question, nodes, xpaths = self.get_empty_question_nodes_and_xpaths_batch()
                for return_type, target_type in zip(tokenizer_return_type, output_tensor_type):
                    output = tokenizer(nodes, xpaths=xpaths, padding=True, return_tensors=return_type)
                    self.assertEqual(output.input_ids.dtype, target_type)