def make_inputs(inp_):
            # Some tests pass in a callable for inp, to generate the inputs
            # (useful if we want to generate complicated aliasing inputs)
            if isinstance(inp_, Callable):
                inp_callable = inp_
                # The callable should return a tuple of f_inputs, f_graph_inputs
                # (The idea is that we might want to compile a function with the graph inputs,
                # but test autograd backprop all the way through the actual inputs)
                with TwoTensorMode() if make_inputs_subclasses else nullcontext():
                    inp, graph_inps = inp_callable()
            else:
                inp = []
                # Our input clones need to mimic when inputs are duplicates of one another
                dupes_map = {}
                for i, x in enumerate(inp_):
                    if x in dupes_map:
                        x_dupe_idx = dupes_map[x]
                        inp.append(inp[x_dupe_idx])
                    else:
                        dupes_map[x] = i
                        if not isinstance(x, torch.Tensor):
                            x_copy = x
                        else:
                            x_copy = x.detach().clone().requires_grad_(x.requires_grad)
                            if x.requires_grad and not x.is_leaf:
                                x_copy = x_copy.clone()

                        inp.append(x_copy)

                if test_mutation:
                    # For graphs where we mutate inputs, need our test to make sure inputs aren't leaves
                    graph_inps = [x.add(1) for x in inp]
                else:
                    graph_inps = inp

            return inp, graph_inps