def test_variable_slice_lora_class_selection(default_vllm_config, dist_init):
    """Test that MergedColumnParallelLinearVariableSliceWithLoRA is selected
    only for nemotron-h style models (checkpoint has single weight but layer
    has 3+ output slices).

    This verifies that from_layer selects
    MergedColumnParallelLinearVariableSliceWithLoRA
    before ColumnParallelLinearWithLoRA for layers with 3+ output sizes, since
    ColumnParallelLinearWithLoRA's slice_lora_b assumes exactly 2 slices.
    """
    from vllm.lora.utils import from_layer

    lora_config = LoRAConfig(max_loras=8, max_lora_rank=8, lora_dtype=torch.float16)

    # Case 1: MergedColumnParallelLinear with 3+ output sizes and
    # packed_modules_list with 1 item (nemotron-h style)
    # -> MergedColumnParallelLinearVariableSliceWithLoRA should be selected
    layer_3_slices = MergedColumnParallelLinear(
        4096, [1024, 1280, 1536], bias=False, params_dtype=torch.float16
    )
    packed_modules_single = ["mlp"]

    assert MergedColumnParallelLinearVariableSliceWithLoRA.can_replace_layer(
        source_layer=layer_3_slices,
        lora_config=lora_config,
        packed_modules_list=packed_modules_single,
    ), "MergedColumnParallelLinearVariableSliceWithLoRA should handle 3+ slices"

    # ColumnParallelLinearWithLoRA should NOT match 3+ slices
    # (its slice_lora_b assumes exactly 2 slices)
    assert not ColumnParallelLinearWithLoRA.can_replace_layer(
        source_layer=layer_3_slices,
        lora_config=lora_config,
        packed_modules_list=packed_modules_single,
    ), (
        "ColumnParallelLinearWithLoRA should NOT handle 3+ slices "
        "(slice_lora_b assumes 2 slices)"
    )

    # Verify from_layer selects the correct class (Variable, not base)
    selected_layer = from_layer(
        layer_3_slices,
        max_loras=8,
        lora_config=lora_config,
        packed_modules_list=packed_modules_single,
    )
    assert isinstance(
        selected_layer, MergedColumnParallelLinearVariableSliceWithLoRA
    ), (
        f"from_layer should select MergedColumnParallelLinearVariableSliceWithLoRA "
        f"for 3+ slices, got {type(selected_layer).__name__}"
    )

    # Case 2: MergedColumnParallelLinear with 2 output sizes and
    # packed_modules_list with 1 item (standard gate_up style)
    # -> ColumnParallelLinearWithLoRA should be selected
    # -> MergedColumnParallelLinearVariableSliceWithLoRA should NOT match
    layer_2_slices = MergedColumnParallelLinear(
        4096, [2048, 2048], bias=False, params_dtype=torch.float16
    )

    assert ColumnParallelLinearWithLoRA.can_replace_layer(
        source_layer=layer_2_slices,
        lora_config=lora_config,
        packed_modules_list=packed_modules_single,
    ), "ColumnParallelLinearWithLoRA should handle 2 slices"

    assert not MergedColumnParallelLinearVariableSliceWithLoRA.can_replace_layer(
        source_layer=layer_2_slices,
        lora_config=lora_config,
        packed_modules_list=packed_modules_single,
    ), "MergedColumnParallelLinearVariableSliceWithLoRA should NOT handle 2 slices"

    # Verify from_layer selects ColumnParallelLinearWithLoRA for 2 slices
    selected_layer_2 = from_layer(
        layer_2_slices,
        max_loras=8,
        lora_config=lora_config,
        packed_modules_list=packed_modules_single,
    )
    assert isinstance(selected_layer_2, ColumnParallelLinearWithLoRA), (
        f"from_layer should select ColumnParallelLinearWithLoRA "
        f"for 2 slices, got {type(selected_layer_2).__name__}"
    )
    # But NOT the Variable subclass
    assert not isinstance(
        selected_layer_2, MergedColumnParallelLinearVariableSliceWithLoRA
    ), (
        "from_layer should NOT select "
        "MergedColumnParallelLinearVariableSliceWithLoRA for 2 slices"
    )

    # Case 3: MergedColumnParallelLinear with 3+ items in packed_modules_list
    # -> MergedColumnParallelLinearVariableSliceWithLoRA should be selected
    packed_modules_three = ["gate_proj", "up_proj", "down_proj"]

    assert MergedColumnParallelLinearVariableSliceWithLoRA.can_replace_layer(
        source_layer=layer_3_slices,
        lora_config=lora_config,
        packed_modules_list=packed_modules_three,
    ), "MergedColumnParallelLinearVariableSliceWithLoRA should handle 3+ packed modules"

    # Case 4: MergedColumnParallelLinear with 2 items in packed_modules_list
    # -> MergedColumnParallelLinearWithLoRA should handle this (not Variable)
    packed_modules_two = ["gate_proj", "up_proj"]

    assert not MergedColumnParallelLinearVariableSliceWithLoRA.can_replace_layer(
        source_layer=layer_2_slices,
        lora_config=lora_config,
        packed_modules_list=packed_modules_two,
    ), (
        "MergedColumnParallelLinearVariableSliceWithLoRA"
        " should NOT handle 2 packed modules"
    )

    assert MergedColumnParallelLinearWithLoRA.can_replace_layer(
        source_layer=layer_2_slices,
        lora_config=lora_config,
        packed_modules_list=packed_modules_two,
    ), "MergedColumnParallelLinearWithLoRA should handle 2 packed modules"

    # Verify from_layer selects MergedColumnParallelLinearWithLoRA for 2 packed modules
    selected_layer_merged = from_layer(
        layer_2_slices,
        max_loras=8,
        lora_config=lora_config,
        packed_modules_list=packed_modules_two,
    )
    assert isinstance(selected_layer_merged, MergedColumnParallelLinearWithLoRA), (
        f"from_layer should select MergedColumnParallelLinearWithLoRA "
        f"for 2 packed modules, got {type(selected_layer_merged).__name__}"
    )

    fully_sharded_tp_lora_config = LoRAConfig(
        max_loras=8,
        max_lora_rank=16,
        lora_dtype=torch.float16,
        fully_sharded_loras=True,
    )
    fully_sharded_tp_layer = MergedColumnParallelLinear(
        4096, [2048, 2048], bias=False, params_dtype=torch.float16
    )
    fully_sharded_tp_layer.tp_size = 2

    assert not MergedColumnParallelLinearWithLoRA.can_replace_layer(
        source_layer=fully_sharded_tp_layer,
        lora_config=fully_sharded_tp_lora_config,
        packed_modules_list=packed_modules_two,
    ), "Generic merged wrapper should reject fully sharded TP layers"

    assert MergedColumnParallelLinearWithShardedLoRA.can_replace_layer(
        source_layer=fully_sharded_tp_layer,
        lora_config=fully_sharded_tp_lora_config,
        packed_modules_list=packed_modules_two,
    ), "Sharded merged wrapper should remain eligible for fully sharded TP layers"

    selected_fully_sharded_tp_layer = from_layer(
        fully_sharded_tp_layer,
        max_loras=8,
        lora_config=fully_sharded_tp_lora_config,
        packed_modules_list=packed_modules_two,
    )
    assert isinstance(
        selected_fully_sharded_tp_layer,
        MergedColumnParallelLinearWithShardedLoRA,
    ), (
        "from_layer should select MergedColumnParallelLinearWithShardedLoRA "
        "for fully sharded TP merged layers, got "
        f"{type(selected_fully_sharded_tp_layer).__name__}"
    )

    # Case 5: DeepSeek's fused_qkv_a_proj should reuse the generic merged
    # wrapper while preserving its custom base forward path.
    deepseek_fused_layer = DeepSeekV2FusedQkvAProjLinear(
        4096, [2048, 2048], prefix="model.layers.0.self_attn.fused_qkv_a_proj"
    )
    selected_deepseek_layer = from_layer(
        deepseek_fused_layer,
        max_loras=8,
        lora_config=lora_config,
        packed_modules_list=packed_modules_two,
    )
    assert isinstance(selected_deepseek_layer, MergedColumnParallelLinearWithLoRA), (
        "from_layer should select MergedColumnParallelLinearWithLoRA "
        f"for DeepSeek fused_qkv_a_proj, got {type(selected_deepseek_layer).__name__}"
    )

    fully_sharded_lora_config = LoRAConfig(
        max_loras=8,
        max_lora_rank=16,
        lora_dtype=torch.float16,
        fully_sharded_loras=True,
    )
    selected_fully_sharded_deepseek_layer = from_layer(
        deepseek_fused_layer,
        max_loras=8,
        lora_config=fully_sharded_lora_config,
        packed_modules_list=packed_modules_two,
    )
    assert isinstance(
        selected_fully_sharded_deepseek_layer,
        MergedColumnParallelLinearWithLoRA,
    ), (
        "from_layer should keep using MergedColumnParallelLinearWithLoRA "
        "for fused_qkv_a_proj when the base layer is effectively unsharded, got "
        f"{type(selected_fully_sharded_deepseek_layer).__name__}"
    )

    # Case 6: Generic subclass of MergedColumnParallelLinear with 2 packed
    # modules should still use the generic merged wrapper.
    class CustomMergedColumnParallelLinear(MergedColumnParallelLinear):
        pass

    custom_merged_layer = CustomMergedColumnParallelLinear(
        4096, [2048, 2048], bias=False, params_dtype=torch.float16
    )
    assert MergedColumnParallelLinearWithLoRA.can_replace_layer(
        source_layer=custom_merged_layer,
        lora_config=lora_config,
        packed_modules_list=packed_modules_two,
    ), "MergedColumnParallelLinearWithLoRA should handle subclasses"

    selected_custom_layer = from_layer(
        custom_merged_layer,
        max_loras=8,
        lora_config=lora_config,
        packed_modules_list=packed_modules_two,
    )
    assert isinstance(selected_custom_layer, MergedColumnParallelLinearWithLoRA), (
        f"from_layer should select MergedColumnParallelLinearWithLoRA "
        f"for subclassed merged layers, got {type(selected_custom_layer).__name__}"
    )

    # Case 7: Plain ColumnParallelLinear (not merged) - common in many models
    # -> ColumnParallelLinearWithLoRA should be selected
    plain_column_parallel = ColumnParallelLinear(
        4096, 4096, bias=False, params_dtype=torch.float16
    )

    assert ColumnParallelLinearWithLoRA.can_replace_layer(
        source_layer=plain_column_parallel,
        lora_config=lora_config,
        packed_modules_list=packed_modules_single,
    ), "ColumnParallelLinearWithLoRA should handle plain ColumnParallelLinear"

    assert not MergedColumnParallelLinearVariableSliceWithLoRA.can_replace_layer(
        source_layer=plain_column_parallel,
        lora_config=lora_config,
        packed_modules_list=packed_modules_single,
    ), (
        "MergedColumnParallelLinearVariableSliceWithLoRA "
        "should NOT handle plain ColumnParallelLinear"
    )

    # Verify from_layer selects ColumnParallelLinearWithLoRA for plain layer
    selected_plain = from_layer(
        plain_column_parallel,
        max_loras=8,
        lora_config=lora_config,
        packed_modules_list=packed_modules_single,
    )
    assert isinstance(selected_plain, ColumnParallelLinearWithLoRA), (
        f"from_layer should select ColumnParallelLinearWithLoRA "
        f"for plain ColumnParallelLinear, got {type(selected_plain).__name__}"
    )

    # Case 8: MergedColumnParallelLinear with exactly 2 output sizes
    # and empty packed_modules_list
    # -> ColumnParallelLinearWithLoRA should NOT match (packed_modules_list != 1)
    # -> MergedColumnParallelLinearVariableSliceWithLoRA should NOT match (< 3 slices)
    assert not ColumnParallelLinearWithLoRA.can_replace_layer(
        source_layer=layer_2_slices,
        lora_config=lora_config,
        packed_modules_list=[],
    ), "ColumnParallelLinearWithLoRA should NOT handle empty packed_modules_list"

    assert not MergedColumnParallelLinearVariableSliceWithLoRA.can_replace_layer(
        source_layer=layer_2_slices,
        lora_config=lora_config,
        packed_modules_list=[],
    ), (
        "MergedColumnParallelLinearVariableSliceWithLoRA "
        "should NOT handle 2 slices even with empty packed_modules_list"
    )