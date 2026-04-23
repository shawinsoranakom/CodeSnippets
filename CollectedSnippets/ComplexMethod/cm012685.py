def write_header(self):
        if V.graph.is_const_graph:
            # We do not write header for constant graph, it will be written by main module.
            return

        if not V.graph.aot_mode:
            self.header.splice(
                '''
                import torch
                from torch._inductor.codecache import CppWrapperCodeCache

                cpp_wrapper_src = (
                r"""
                '''
            )

        for device in V.graph.device_types:
            if device != "meta":
                self.add_device_include(device)

        if V.graph.aot_mode:
            if config.aot_inductor.dynamic_linkage:
                with open(
                    os.path.join(
                        os.path.dirname(__file__), "aoti_runtime", "interface.cpp"
                    )
                ) as f:
                    self.header.splice(f.read())
            else:
                # we produce a separate model header for each model in static linkage
                self.header.splice(f"""#include \"{self.model_class_name_suffix}.h\"""")
            self.header.splice("\n")

        if config.cpp.enable_kernel_profile:
            self.header.splice(
                "#include <torch/csrc/inductor/aoti_runtime/kernel_context_tls.h>"
            )
            self.header.splice(
                """
                namespace torch::aot_inductor {
                thread_local KernelContext* tls_kernel_context = nullptr;
                }
                """
            )