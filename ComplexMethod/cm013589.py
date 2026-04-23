def __exit__(
        self,
        type: type[BaseException] | None,
        value: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if not self.active:
            return
        for gm in self.copied_gms + [self.gm]:
            gm._unregister_create_node_hook(self._node_creation_hook)
            gm._unregister_erase_node_hook(self._node_erase_hook)
            gm._unregister_replace_node_hook(self._node_replace_hook)
            gm._unregister_deepcopy_hook(self._deepcopy_hook)

        if self.log_url is None:
            return

        if len(self.created_nodes) > 0 or len(self.erased_nodes) > 0:
            for e in self.input_dot_graph.get_node_list():
                if e.get_name() in self.erased_nodes:
                    e.obj_dict["attributes"]["fillcolor"] = "yellow"
                else:
                    e.obj_dict["attributes"]["fillcolor"] = "grey"
            if self.log_url is None:
                raise AssertionError("log_url is not set")
            self.input_dot_graph.write(
                os.path.join(
                    self.log_url,
                    f"pass_{GraphTransformObserver.__pass_count}_{self.passname}_input_graph.dot",
                )
            )

            output_dot_graph = FxGraphDrawer(
                self.gm,
                self.passname,
                ignore_getattr=True,
                ignore_parameters_and_buffers=True,
            ).get_dot_graph()
            for e in output_dot_graph.get_node_list():
                if e.get_name() in self.created_nodes:
                    e.obj_dict["attributes"]["fillcolor"] = "yellow"
                else:
                    e.obj_dict["attributes"]["fillcolor"] = "grey"
            output_dot_graph.write(
                os.path.join(
                    self.log_url,
                    f"pass_{GraphTransformObserver.__pass_count}_{self.passname}_output_graph.dot",
                )
            )