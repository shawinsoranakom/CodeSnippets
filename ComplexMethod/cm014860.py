def validate_transformed_module(
            # To please flake
            self,
            pattern_count_map,
            data_shape,
            prepack_removal=False,
            fuse_clamping_ops=False):
        module_instance = self
        scripted_model = torch.jit.script(module_instance)
        scripted_model.eval()
        input_data = torch.normal(1, 20, size=data_shape)
        scripted_model(input_data)
        torch._C._jit_pass_metal_insert_prepacked_ops(scripted_model._c)
        if fuse_clamping_ops or prepack_removal:
            scripted_model._c = torch._C._freeze_module(scripted_model._c)
        if fuse_clamping_ops:
            torch._C._jit_pass_metal_fuse_clamp_w_prepacked_conv(scripted_model._c)
        if prepack_removal:
            torch._C._jit_pass_metal_fold_prepacking_ops(scripted_model._c)

        buffer = io.BytesIO()
        torch.jit.save(scripted_model, buffer)
        buffer.seek(0)
        deserialized_scripted_model = torch.jit.load(buffer)
        for pattern, v in pattern_count_map.items():
            if (v == 0):
                FileCheck().check(pattern).run(deserialized_scripted_model.graph)
            elif (v == -1):
                FileCheck().check_not(pattern).run(deserialized_scripted_model.graph)
            else:
                FileCheck().check_count(pattern, v, exactly=True).run(deserialized_scripted_model.graph)