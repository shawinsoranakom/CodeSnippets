def go(node: fx.Node, keypath: tuple[object, ...]) -> fx.Node:
                        if keypath == ():
                            return node
                        if (
                            len(keypath) >= 2
                            and isinstance(keypath[0], CallMethodKey)
                            and isinstance(keypath[1], pytree.SequenceKey)
                        ):
                            if keypath[0].name == "size":
                                return go(
                                    graph.call_function(
                                        torch.ops.aten.sym_size.int,
                                        (node, keypath[1].idx),
                                    ),
                                    keypath[2:],
                                )
                            if keypath[0].name == "stride":
                                return go(
                                    graph.call_function(
                                        torch.ops.aten.sym_stride.int,
                                        (node, keypath[1].idx),
                                    ),
                                    keypath[2:],
                                )

                            return go(
                                graph.call_method(
                                    keypath[0].name, (node, keypath[1].idx)
                                ),
                                keypath[2:],
                            )
                        elif isinstance(keypath[0], CallMethodKey):
                            if keypath[0].name == "storage_offset":
                                return go(
                                    graph.call_function(
                                        torch.ops.aten.sym_storage_offset.default,
                                        (node,),
                                    ),
                                    keypath[1:],
                                )

                            return go(
                                graph.call_method(keypath[0].name, (node,)), keypath[1:]
                            )
                        elif isinstance(keypath[0], pytree.SequenceKey):
                            return go(
                                graph.call_function(
                                    operator.getitem, (node, keypath[0].idx)
                                ),
                                keypath[1:],
                            )
                        elif isinstance(keypath[0], ConvertIntKey):
                            return go(
                                graph.call_function(torch.sym_ite, (node, 1, 0)),
                                keypath[1:],
                            )
                        elif isinstance(keypath[0], DivideByKey):
                            # TODO: need to assert divisibility
                            return go(
                                graph.call_function(
                                    operator.floordiv, (node, keypath[0].divisor)
                                ),
                                keypath[1:],
                            )
                        elif isinstance(keypath[0], InnerTensorKey):
                            return go(
                                graph.call_function(
                                    getattr, (node, keypath[0].inner_name)
                                ),
                                keypath[1:],
                            )
                        else:
                            raise AssertionError(f"unrecognized keypath {keypath}")