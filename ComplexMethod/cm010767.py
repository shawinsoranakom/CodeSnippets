def flattened_joint(*args: Any) -> Any:
            # The idea here is that the joint graph that AOTAutograd creates has some strict properties:
            # (1) It accepts two arguments (primals, tangents), and pytree_flattens them
            # (2) It returns a tuple of (fw_outs, gradients)
            # This is a very useful convention for anyone who wants to partition the joint graph
            # into a separate forward and backward graph.
            # However,
            # (1) for people exporting a single joint graph, it would be preferable not to have
            #     any pytrees in the graph.
            # (2) We are guaranteed in the aot_export_module case that the forward outputs a loss,
            #     and there are therefore no tangents that are needed to run the joint graph.
            # (3) AOTAutograd creates a grad_input for every input in the forward,
            #     including None's for inputs that are not grad-requiring tensors.
            #     we don't want these in our export graph.
            #     and there are therefore no tangents that are needed to run the joint graph.
            # This function "fixes" both of the above by removing any tangent inputs,
            # and removing pytrees from the original FX graph.
            fake_tangents = [
                None
                for _ in range(
                    metadata.num_outputs + metadata.num_mutated_inp_runtime_indices
                )
            ]
            fw_outs, gradients = fx_g(args, fake_tangents)
            if len(gradients) != len(args):
                raise AssertionError(
                    f"len(gradients)={len(gradients)} != len(args)={len(args)}"
                )
            output_gradients = []
            for a, grad in zip(args, gradients):
                if isinstance(a, torch.Tensor) and a.requires_grad:
                    if grad is None:
                        raise AssertionError("""\
Found a parameter that did not receive a gradient.
"This is most likely a bug, but if this needs to be supported please comment on this Github issue:
https://github.com/pytorch/pytorch/issues/101192
""")
                    output_gradients.append(grad)
                else:
                    if grad is not None:
                        raise AssertionError(
                            f"expected grad to be None for non-tensor or non-requires_grad input, got {type(grad)}"
                        )
            return *fw_outs, *output_gradients