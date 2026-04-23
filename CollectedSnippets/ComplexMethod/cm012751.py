def emit(self, operation):
            """Given a gem operation, emits a template definition of the operation"""

            opcode_class_main = operation.tile_description.math_instruction.opcode_class
            opcode_class_epi = opcode_class_main

            tile_shape = operation.tile_description.tile_shape
            instruction_shape = (
                operation.tile_description.math_instruction.instruction_shape
            )
            cluster_m = operation.tile_description.cluster_shape[0]
            cluster_n = operation.tile_description.cluster_shape[1]

            tile_shape_m, tile_shape_n, tile_shape_k = tile_shape

            # account for static/dynamic cluster shapes
            cta_m = tile_shape[0] // cluster_m if cluster_m > 0 else tile_shape[0]
            cta_n = tile_shape[1] // cluster_n if cluster_n > 0 else tile_shape[1]

            # Shape passed to epilogue builder
            is_sm100_kernel = operation.arch == 100
            if is_sm100_kernel:
                cta_m_per_mma_instruction = (
                    2 if "2sm" in operation.procedural_name() else 1
                )
                if cluster_m <= 0:
                    cta_m = cta_m // cta_m_per_mma_instruction

                if opcode_class_main in [
                    OpcodeClass.TensorOp,
                    OpcodeClass.BlockScaledTensorOp,
                ]:
                    tile_shape_m = instruction_shape[0]
                    tile_shape_n = instruction_shape[1]

            # stage count set to zero indicates builder automatic stage selection
            if operation.tile_description.stages > 0:
                stage_count_string = f"cutlass::gemm::collective::StageCount<\
{str(operation.tile_description.stages)}>"
            else:
                stage_count_string = (
                    f"cutlass::gemm::collective::StageCountAutoCarveout<static_cast<int>(\
sizeof(typename {str(operation.procedural_name())}_epilogue::SharedStorage))>"
                )
            if self.device_type == "xpu":
                stage_count_string = "cutlass::gemm::collective::StageCountAuto"

            epi_tile_mn = "cutlass::epilogue::collective::EpilogueTileAuto"

            (
                instance_layout_A,
                instance_layout_B,
                instance_layout_C,
                instance_layout_D,
            ) = (
                operation.A.layout,
                operation.B.layout,
                operation.C.layout,
                operation.D.layout,
            )

            # 3.0 profiler integration only supports trivial epilogues for now
            epilogue_vector_length = 1

            # Support built-in epilogue functors or user-defined functions
            if isinstance(operation.epilogue_functor, enum.Enum):
                values = {
                    "element_epilogue": str(DataTypeTag[operation.element_epilogue]),
                    "epilogue_functor": EpilogueFunctor3xTag[
                        operation.epilogue_functor
                    ],
                }
                epilogue_functor = SubstituteTemplate(
                    self.builtin_epilogue_functor_template, values
                )

                if (
                    is_block_scaled(operation.gemm_kind)
                    and operation.ScaleFactorD.element != DataType.void
                ):
                    epilogue_functor = self.emit_block_scale_epilogue_functor(operation)
            else:
                epilogue_functor = self.epilogue_functor.emit_declaration()

            if (
                is_block_scaled(operation.gemm_kind)
                and operation.ScaleFactorD.element != DataType.void
            ):
                epilogue_functor = self.emit_block_scale_epilogue_functor(operation)

            #
            # Cutlass3x complex kernels' ElementA(B) is a tuple in collective mainloop builder,
            # e.g. cute::tuple<Element, Transform>, Transform : cute::identity / cute::conjugate.
            element_a = (
                DataTypeTag[operation.A.element]
                if not operation.is_complex()
                else f"cute::tuple<{str(DataTypeTag[operation.A.element])},\
{str(ComplexTransformTag3x[operation.A.complex_transform])}>"
            )
            element_b = (
                DataTypeTag[operation.B.element]
                if not operation.is_complex()
                else f"cute::tuple<{str(DataTypeTag[operation.B.element])},\
{str(ComplexTransformTag3x[operation.B.complex_transform])}>"
            )
            epilogue_schedule_type = EpilogueScheduleTag[operation.epilogue_schedule]

            if opcode_class_main == OpcodeClass.BlockScaledTensorOp:
                is_no_smem_epilogue = operation.epilogue_schedule in [
                    EpilogueScheduleType.NoSmemWarpSpecialized1Sm,
                    EpilogueScheduleType.NoSmemWarpSpecialized2Sm,
                ]
                grouped = is_grouped(operation.gemm_kind)
                if cta_n == 256 and operation.kernel_schedule == to_grouped_schedule(
                    KernelScheduleType.Nvf4TmaWarpSpecialized1SmSm100, grouped
                ):
                    epi_tile_mn = "cute::Shape<cute::_128,cute::_64>"
                    if not is_no_smem_epilogue:
                        epilogue_schedule_type = EpilogueScheduleTag[
                            to_grouped_schedule(
                                EpilogueScheduleType.TmaWarpSpecialized1Sm, grouped
                            )
                        ]
                if cta_n == 256 and operation.kernel_schedule == to_grouped_schedule(
                    KernelScheduleType.Nvf4TmaWarpSpecialized2SmSm100, grouped
                ):
                    epi_tile_mn = "cute::Shape<cute::_128,cute::_64>"
                    if not is_no_smem_epilogue:
                        epilogue_schedule_type = EpilogueScheduleTag[
                            to_grouped_schedule(
                                EpilogueScheduleType.TmaWarpSpecialized2Sm, grouped
                            )
                        ]
                element_a = f"cute::tuple<{str(element_a)},{str(DataTypeTag[operation.ScaleFactorA])}>"
                element_b = f"cute::tuple<{str(element_b)},{str(DataTypeTag[operation.ScaleFactorB])}>"

            operation_name_str = operation.procedural_name()
            layout_a_str = LayoutTag[instance_layout_A]
            layout_b_str = LayoutTag[instance_layout_B]
            mixed_dtype_prepare_code = ""
            if operation.mixed_input_mode is not None:
                A_dtype = operation.A.element
                B_dtype = operation.B.element
                A_dtype_bits = DataTypeSize[A_dtype]
                B_dtype_bits = DataTypeSize[B_dtype]
                is_A_dtype_narrow = A_dtype_bits < B_dtype_bits
                if is_A_dtype_narrow:
                    narrow_dtype, wide_dtype = (A_dtype, B_dtype)
                    narrow_dtype_bits, wide_dtype_bits = (A_dtype_bits, B_dtype_bits)
                else:
                    narrow_dtype, wide_dtype = (B_dtype, A_dtype)
                    narrow_dtype_bits, wide_dtype_bits = (B_dtype_bits, A_dtype_bits)

                narrow_tag = DataTypeTag[narrow_dtype]
                wide_tag = DataTypeTag[wide_dtype]
                scale_tag = DataTypeTag[wide_dtype]
                zero_tag = DataTypeTag[wide_dtype]

                do_shuffle = False
                value_shuffle_str = ""
                if narrow_dtype_bits == 4 and wide_dtype_bits == 16:
                    value_shuffle_str = "cute::Layout<cute::Shape<cute::_2,cute::_4>, \
cute::Stride<cute::_4,cute::_1>>"
                    do_shuffle = True
                if narrow_dtype_bits == 8 and wide_dtype_bits == 16:
                    value_shuffle_str = "cute::Layout<cute::Shape<cute::_2,cute::_2>, \
cute::Stride<cute::_2,cute::_1>>"
                    do_shuffle = True
                do_shuffle = operation.mixed_input_shuffle and do_shuffle

                if do_shuffle:
                    if is_A_dtype_narrow:
                        stride_narrow_str = (
                            f"cutlass::detail::TagToStrideA_t<{layout_a_str}>"
                        )
                        layout_a_str = f"{operation_name_str}_LayoutNarrowReordered"
                    else:
                        stride_narrow_str = (
                            f"cutlass::detail::TagToStrideB_t<{layout_b_str}>"
                        )
                        layout_b_str = f"{operation_name_str}_LayoutNarrowReordered"
                    # The {operation_name_str}_ prefixs in mixed_dtype_prepare_code and
                    # layout_{a, b}_str are to prevent errors in Windows platform unity build
                    mixed_dtype_prepare_code = f"""
            using {operation_name_str}_StrideNarrow = {stride_narrow_str};
            using {operation_name_str}_ValueShuffle = {value_shuffle_str};
            static constexpr int {operation_name_str}_NumShuffleAtoms = 1;
            using {operation_name_str}_MmaAtomShape = \
cute::Layout<cute::Shape<cute::_1, cute::Int<{operation_name_str}_NumShuffleAtoms>>>;
            using {operation_name_str}_LayoutAtomQuant = \
decltype(cutlass::compute_memory_reordering_atom<{wide_tag}, {operation_name_str}_MmaAtomShape, \
{operation_name_str}_ValueShuffle>());
            using {operation_name_str}_LayoutNarrowReordered = \
decltype(cute::tile_to_shape({operation_name_str}_LayoutAtomQuant{{}}, \
cute::Layout<cute::Shape<int,int,int>, {operation_name_str}_StrideNarrow>{{}}));
                    """

                mixed_input_modes_to_element = {
                    MixedInputMode.ConvertOnly: narrow_tag,
                    MixedInputMode.ScaleOnly: f"cute::tuple<{narrow_tag}, {scale_tag}>",
                    MixedInputMode.ScaleWithZeroPoint: f"cute::tuple<{narrow_tag}, {scale_tag}, {zero_tag}>",
                }
                narrow_element = mixed_input_modes_to_element.get(
                    operation.mixed_input_mode, narrow_tag
                )

                if narrow_dtype == DataType.s4 and (
                    wide_dtype == DataType.e4m3 or wide_dtype == DataType.e5m2
                ):
                    narrow_element = (
                        f"cute::tuple<{narrow_tag}, cutlass::Array<{scale_tag}, 8>>"
                    )

                if is_A_dtype_narrow:
                    element_a = narrow_element
                else:
                    element_b = narrow_element

            if self.evt_name:
                epilogue_functor = self.evt_name

            if self.device_type == "xpu":
                arch = f"cutlass::arch::Xe{operation.arch}"
            else:
                arch = f"cutlass::arch::Sm{operation.arch}"

            values = {
                "operation_name": operation_name_str,
                "operation_suffix": self.operation_suffix,
                "problem_shape": self.problem_shape(operation),
                "element_a": element_a,
                "layout_a": self.pointerize_if_grouped(operation, layout_a_str),
                "element_b": element_b,
                "layout_b": self.pointerize_if_grouped(operation, layout_b_str),
                "element_c": DataTypeTag[operation.C.element],
                "layout_c": self.pointerize_if_grouped(
                    operation, LayoutTag[instance_layout_C]
                ),
                "element_d": DataTypeTag[operation.D.element],
                "layout_d": self.pointerize_if_grouped(
                    operation, LayoutTag[instance_layout_D]
                ),
                "element_accumulator": DataTypeTag[operation.accumulator_type()],
                "opcode_class_main": OpcodeClassTag[opcode_class_main],
                "opcode_class_epi": OpcodeClassTag[opcode_class_epi],
                "arch": arch,
                "tile_shape_m": str(tile_shape_m),
                "tile_shape_n": str(tile_shape_n),
                "tile_shape_k": str(tile_shape_k),
                "cluster_shape_m": "cute::_"
                + str(operation.tile_description.cluster_shape[0])
                if operation.tile_description.cluster_shape[0] > 0
                else "int",
                "cluster_shape_n": "cute::_"
                + str(operation.tile_description.cluster_shape[1])
                if operation.tile_description.cluster_shape[1] > 0
                else "int",
                "cluster_shape_k": "cute::_"
                + str(operation.tile_description.cluster_shape[2])
                if operation.tile_description.cluster_shape[2] > 0
                else "int",
                "instruction_shape_m": str(instruction_shape[0]),
                "instruction_shape_n": str(instruction_shape[1]),
                "instruction_shape_k": str(instruction_shape[2]),
                "kernel_schedule": str(KernelScheduleTag[operation.kernel_schedule]),
                "epilogue_schedule": str(epilogue_schedule_type),
                "epi_tile_mn": epi_tile_mn,
                "epilogue_functor": epilogue_functor,
                "stages": stage_count_string,
                "align_a": str(operation.A.alignment),
                "align_b": str(operation.B.alignment),
                "align_c": str(operation.C.alignment),
                "align_d": str(operation.D.alignment),
                "transform_a": ComplexTransformTag[operation.A.complex_transform],
                "transform_b": ComplexTransformTag[operation.B.complex_transform],
                "math_operation": MathOperationTag[
                    operation.tile_description.math_instruction.math_operation
                ],
                "epilogue_vector_length": str(epilogue_vector_length),
                "element_epilogue": str(DataTypeTag[operation.element_epilogue]),
                "tile_scheduler": str(TileSchedulerTag[operation.tile_scheduler]),
                "mixed_dtype_prepare_code": mixed_dtype_prepare_code,
            }

            return SubstituteTemplate(self.gemm_template, values)