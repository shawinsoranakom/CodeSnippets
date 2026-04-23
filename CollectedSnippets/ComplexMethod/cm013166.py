def get_new_module_tests():
    common_utils.set_rng_seed()
    new_module_tests = [
        poissonnllloss_no_reduce_test(),
        bceloss_no_reduce_test(),
        bceloss_weights_no_reduce_test(),
        bce_with_logistic_legacy_enum_test(),
        bce_with_logistic_no_reduce_test(),
        bceloss_no_reduce_scalar_test(),
        bceloss_weights_no_reduce_scalar_test(),
        bce_with_logistic_no_reduce_scalar_test(),
        kldivloss_with_target_no_reduce_test(),
        kldivloss_no_reduce_test(),
        kldivloss_no_reduce_scalar_test(),
        kldivloss_with_log_target_no_reduce_test(),
        kldivloss_no_reduce_log_target_test(),
        kldivloss_no_reduce_scalar_log_target_test(),
        l1loss_no_reduce_test(),
        l1loss_no_reduce_complex_test(),
        l1loss_no_reduce_scalar_test(),
        mseloss_no_reduce_test(),
        mseloss_no_reduce_scalar_test(),
        nllloss_no_reduce_test(),
        nllloss_no_reduce_ignore_index_test(),
        nllloss_no_reduce_weights_test(),
        nllloss_no_reduce_weights_ignore_index_test(),
        nllloss_no_reduce_weights_ignore_index_neg_test(),
        nllloss2d_no_reduce_test(),
        nllloss2d_no_reduce_weights_test(),
        nllloss2d_no_reduce_ignore_index_test(),
        nlllossNd_no_reduce_test(),
        nlllossNd_no_reduce_weights_test(),
        nlllossNd_no_reduce_ignore_index_test(),
        smoothl1loss_no_reduce_test(),
        smoothl1loss_no_reduce_scalar_test(),
        smoothl1loss_beta_test(),
        smoothl1loss_zero_beta_test(),
        huberloss_delta_test(),
        multilabelmarginloss_0d_no_reduce_test(),
        multilabelmarginloss_1d_no_reduce_test(),
        multilabelmarginloss_index_neg_test(),
        multilabelmarginloss_no_reduce_test(),
        hingeembeddingloss_no_reduce_test(),
        hingeembeddingloss_margin_no_reduce_test(),
        softmarginloss_no_reduce_test(),
        multilabelsoftmarginloss_no_reduce_test(),
        multilabelsoftmarginloss_weights_no_reduce_test(),
        multimarginloss_no_reduce_test(),
        multimarginloss_1d_no_reduce_test(),
        multimarginloss_1d_input_0d_target_no_reduce_test(),
        multimarginloss_p_no_reduce_test(),
        multimarginloss_margin_no_reduce_test(),
        multimarginloss_weights_no_reduce_test(),
        dict(
            module_name='Conv1d',
            constructor_args=(4, 5, 3),
            cpp_constructor_args='torch::nn::Conv1dOptions(4, 5, 3)',
            input_size=(2, 4, 10),
            cudnn=True,
            with_tf32=True,
            tf32_precision=0.005,
            default_dtype=torch.double,
        ),
        dict(
            module_name='Conv1d',
            constructor_args=(4, 5, 3, 2),
            cpp_constructor_args='torch::nn::Conv1dOptions(4, 5, 3).stride(2)',
            input_size=(2, 4, 10),
            cudnn=True,
            desc='stride',
            with_tf32=True,
            tf32_precision=0.005,
            default_dtype=torch.double,
        ),
        dict(
            module_name='Conv1d',
            constructor_args=(4, 5, 3, 1, 1),
            cpp_constructor_args='torch::nn::Conv1dOptions(4, 5, 3).stride(1).padding(1)',
            input_size=(2, 4, 10),
            cudnn=True,
            desc='pad1',
            with_tf32=True,
            tf32_precision=0.01,
            default_dtype=torch.double,
        ),
        dict(
            module_name='Conv1d',
            constructor_args=(4, 5, 5, 1, 2),
            cpp_constructor_args='torch::nn::Conv1dOptions(4, 5, 5).stride(1).padding(2)',
            input_size=(2, 4, 10),
            cudnn=True,
            desc='pad2',
            with_tf32=True,
            tf32_precision=0.005,
            default_dtype=torch.double,
        ),
        dict(
            module_name='Conv1d',
            constructor_args=(4, 4, 3, 1, 1),
            cpp_constructor_args='torch::nn::Conv1dOptions(4, 4, 3).stride(1).padding(1)',
            input_size=(1, 4, 1),
            cudnn=True,
            desc='pad1size1',
            with_tf32=True,
            tf32_precision=0.005,
            default_dtype=torch.double,
        ),
        dict(
            module_name='Conv1d',
            constructor_args=(4, 4, 5, 1, 2),
            cpp_constructor_args='torch::nn::Conv1dOptions(4, 4, 5).stride(1).padding(2)',
            input_size=(1, 4, 1),
            cudnn=True,
            desc='pad2size1',
            with_tf32=True,
            tf32_precision=0.005,
            default_dtype=torch.double,
        ),
        dict(
            module_name='Conv1d',
            constructor_args=(4, 5, 3),
            cpp_constructor_args='torch::nn::Conv1dOptions(4, 5, 3)',
            input_size=(0, 4, 10),
            cudnn=True,
            desc='zero_batch',
            with_tf32=True,
            tf32_precision=0.005,
        ),
        dict(
            fullname='Conv1d_dilated',
            constructor=lambda: nn.Conv1d(4, 5, kernel_size=3, dilation=2),
            cpp_constructor_args='torch::nn::Conv1dOptions(4, 5, 3).dilation(2)',
            input_size=(2, 4, 10),
            with_tf32=True,
            tf32_precision=0.005,
            default_dtype=torch.double,
        ),
        dict(
            fullname='Conv1d_groups',
            constructor=lambda: nn.Conv1d(4, 6, kernel_size=3, groups=2),
            cpp_constructor_args='torch::nn::Conv1dOptions(4, 6, 3).groups(2)',
            input_size=(2, 4, 6),
            cudnn=True,
            with_tf32=True,
            tf32_precision=0.005,
            default_dtype=torch.double,
        ),
        dict(
            fullname='Conv1d_pad_valid',
            constructor=lambda: nn.Conv1d(4, 5, 3, padding="valid"),
            cpp_constructor_args='torch::nn::Conv1dOptions(4, 5, 3).padding(torch::kValid)',
            input_size=(2, 4, 10),
            cudnn=True,
            with_tf32=True,
            tf32_precision=0.005,
            default_dtype=torch.double,
        ),
        dict(
            fullname='Conv1d_pad_same',
            constructor=lambda: nn.Conv1d(4, 5, 3, padding="same"),
            cpp_constructor_args='torch::nn::Conv1dOptions(4, 5, 3).padding(torch::kSame)',
            input_size=(2, 4, 10),
            cudnn=True,
            with_tf32=True,
            tf32_precision=0.005,
            default_dtype=torch.double,
        ),
        dict(
            fullname='Conv1d_pad_same2',
            constructor=lambda: nn.Conv1d(4, 5, 4, padding="same"),
            cpp_constructor_args='torch::nn::Conv1dOptions(4, 5, 4).padding(torch::kSame)',
            input_size=(2, 4, 10),
            cudnn=True,
            with_tf32=True,
            tf32_precision=0.005,
            default_dtype=torch.double,
        ),
        dict(
            fullname='Conv1d_pad_same_dilated',
            constructor=lambda: nn.Conv1d(4, 5, 4, padding="same", dilation=2),
            cpp_constructor_args='torch::nn::Conv1dOptions(4, 5, 3).padding(torch::kSame).dilation(2)',
            input_size=(2, 4, 10),
            cudnn=True,
            with_tf32=True,
            tf32_precision=0.005,
            default_dtype=torch.double,
        ),
        dict(
            fullname='ConvTranspose1d',
            constructor=lambda: nn.ConvTranspose1d(3, 4, kernel_size=3, stride=(3,), padding=1, output_padding=(1,)),
            cpp_constructor_args='torch::nn::ConvTranspose1dOptions(3, 4, 3).stride(3).padding(1).output_padding(1)',
            cudnn=True,
            input_size=(1, 3, 7),
            with_tf32=True,
            tf32_precision=0.005,
            default_dtype=torch.double,
        ),
        dict(
            module_name='ConvTranspose1d',
            constructor_args=(3, 4, 3, 2, 1, 1, 1, False),
            cpp_constructor_args='''torch::nn::ConvTranspose1dOptions(3, 4, 3)
                                    .stride(2).padding(1).output_padding(1).groups(1).bias(false)''',
            input_size=(1, 3, 6),
            cudnn=True,
            desc='no_bias',
            with_tf32=True,
            tf32_precision=0.005,
            default_dtype=torch.double,
        ),
        dict(
            module_name='ConvTranspose1d',
            constructor_args=(3, 4, 3, 2, 1, 1, 1, True, 2),
            cpp_constructor_args='''torch::nn::ConvTranspose1dOptions(3, 4, 3)
                                    .stride(2).padding(1).output_padding(1).groups(1).bias(true).dilation(2)''',
            input_size=(1, 3, 6),
            cudnn=True,
            desc='dilated',
            with_tf32=True,
            tf32_precision=0.005,
            default_dtype=torch.double,
        ),
        dict(
            fullname='ConvTranspose1d_groups',
            constructor=lambda: nn.ConvTranspose1d(4, 6, 3, stride=(3,), padding=1, output_padding=(1,), groups=2),
            cpp_constructor_args='''torch::nn::ConvTranspose1dOptions(4, 6, 3)
                                    .stride(3).padding(1).output_padding(1).groups(2)''',
            cudnn=True,
            input_size=(2, 4, 7),
            with_tf32=True,
            tf32_precision=0.005,
            default_dtype=torch.double,
        ),
        dict(
            module_name='Conv2d',
            constructor_args=(3, 4, (3, 2)),
            cpp_constructor_args='torch::nn::Conv2dOptions(3, 4, {3, 2})',
            input_size=(2, 3, 7, 5),
            cudnn=True,
            check_with_long_tensor=True,
            with_tf32=True,
            tf32_precision=0.005,
            default_dtype=torch.double,
        ),
        dict(
            module_name='Conv2d',
            constructor_args=(3, 4, (3, 3), (2, 2)),
            cpp_constructor_args='torch::nn::Conv2dOptions(3, 4, {3, 3}).stride({2, 2})',
            input_size=(2, 3, 6, 6),
            cudnn=True,
            desc='strided',
            check_with_long_tensor=True,
            with_tf32=True,
            tf32_precision=0.005,
            default_dtype=torch.double,
        ),
        dict(
            module_name='Conv2d',
            constructor_args=(3, 4, (3, 3), (2, 2), (1, 1)),
            cpp_constructor_args='torch::nn::Conv2dOptions(3, 4, {3, 3}).stride({2, 2}).padding({1, 1})',
            input_size=(2, 3, 6, 6),
            cudnn=True,
            desc='padding',
            check_with_long_tensor=True,
            with_tf32=True,
            tf32_precision=0.005,
            default_dtype=torch.double,
        ),
        dict(
            module_name='Conv2d',
            constructor_args=(3, 2, (3, 3), (2, 2), (1, 1), (2, 2)),
            cpp_constructor_args='torch::nn::Conv2dOptions(3, 2, {3, 3}).stride({2, 2}).padding({1, 1}).dilation({2, 2})',
            input_size=(2, 3, 8, 8),
            cudnn=True,
            desc='dilated',
            check_with_long_tensor=True,
            with_tf32=True,
            tf32_precision=0.005,
            default_dtype=torch.double,
        ),
        dict(
            module_name='Conv2d',
            constructor_args=(3, 4, (3, 2), 1, 0, 1, 1, False),
            cpp_constructor_args='''torch::nn::Conv2dOptions(3, 4, {3, 2})
                                    .stride(1).padding(0).dilation(1).groups(1).bias(false)''',
            input_size=(2, 3, 6, 5),
            cudnn=True,
            desc='no_bias',
            check_with_long_tensor=True,
            with_tf32=True,
            tf32_precision=0.015,
            default_dtype=torch.double,
        ),
        dict(
            module_name='Conv2d',
            constructor_args=(3, 4, (3, 2)),
            cpp_constructor_args='torch::nn::Conv2dOptions(3, 4, {3, 2})',
            input_size=(0, 3, 7, 5),
            cudnn=True,
            desc='zero_batch',
            check_with_long_tensor=True,
            with_tf32=True,
        ),
        dict(
            fullname='Conv2d_groups',
            constructor=lambda: nn.Conv2d(4, 6, (3, 2), groups=2),
            cpp_constructor_args='torch::nn::Conv2dOptions(4, 6, {3, 2}).groups(2)',
            input_size=(2, 4, 6, 5),
            cudnn=True,
            check_with_long_tensor=True,
            with_tf32=True,
            tf32_precision=0.015,
            default_dtype=torch.double,
        ),
        dict(
            fullname='Conv2d_groups_thnn',
            constructor=lambda: nn.Conv2d(4, 6, (3, 2), groups=2),
            cpp_constructor_args='torch::nn::Conv2dOptions(4, 6, {3, 2}).groups(2)',
            input_size=(2, 4, 6, 5),
            check_with_long_tensor=True,
            with_tf32=True,
            tf32_precision=0.015,
            default_dtype=torch.double,
        ),
        dict(
            fullname='Conv2d_pad_valid',
            constructor=lambda: nn.Conv2d(2, 4, (3, 4), padding="valid"),
            cpp_constructor_args='torch::nn::Conv2dOptions(2, 4, {3, 4}).padding(torch::kValid)',
            input_size=(2, 2, 6, 5),
            cudnn=True,
            with_tf32=True,
            tf32_precision=0.005,
            default_dtype=torch.double,
        ),
        dict(
            fullname='Conv2d_pad_same',
            constructor=lambda: nn.Conv2d(2, 4, (3, 4), padding="same"),
            cpp_constructor_args='torch::nn::Conv2dOptions(2, 4, {3, 4}).padding(torch::kSame)',
            input_size=(2, 2, 6, 5),
            cudnn=True,
            with_tf32=True,
            tf32_precision=0.01,
            default_dtype=torch.double,
        ),
        dict(
            fullname='Conv2d_pad_same_dilated',
            constructor=lambda: nn.Conv2d(2, 4, (3, 4), padding="same", dilation=2),
            cpp_constructor_args='torch::nn::Conv2dOptions(2, 4, {3, 4}).padding(torch::kSame).dilation(2)',
            input_size=(2, 2, 6, 5),
            cudnn=True,
            with_tf32=True,
            tf32_precision=0.01,
            default_dtype=torch.double,
        ),
        dict(
            module_name='ConvTranspose2d',
            constructor_args=(3, 4, 3, (3, 2), 1, (1, 1)),
            cpp_constructor_args='''torch::nn::ConvTranspose2dOptions(3, 4, 3)
                                    .stride({3, 2}).padding(1).output_padding({1, 1})''',
            cudnn=True,
            input_size=(1, 3, 7, 6),
            check_with_long_tensor=True,
            with_tf32=True,
            tf32_precision=0.01,
            default_dtype=torch.double,
        ),
        dict(
            module_name='ConvTranspose2d',
            constructor_args=(3, 4, 3, (2, 3), 1, (1, 1), 1, False, (2, 2)),
            cpp_constructor_args='''torch::nn::ConvTranspose2dOptions(3, 4, 3)
                                    .stride({2, 3})
                                    .padding(1)
                                    .output_padding({1, 1})
                                    .groups(1)
                                    .bias(false)
                                    .dilation({2, 2})''',
            input_size=(1, 3, 6, 7),
            cudnn=True,
            desc='dilated',
            check_with_long_tensor=True,
            with_tf32=True,
            tf32_precision=0.01,
            default_dtype=torch.double,
        ),
        dict(
            module_name='ConvTranspose2d',
            constructor_args=(3, 4, 3, (2, 3), 1, (1, 1), 1, False),
            cpp_constructor_args='''torch::nn::ConvTranspose2dOptions(3, 4, 3)
                                    .stride({2, 3}).padding(1).output_padding({1, 1}).groups(1).bias(false)''',
            input_size=(1, 3, 6, 7),
            cudnn=True,
            desc='no_bias',
            check_with_long_tensor=True,
            with_tf32=True,
            tf32_precision=0.01,
            default_dtype=torch.double,
        ),
        dict(
            fullname='ConvTranspose2d_groups',
            constructor=lambda: nn.ConvTranspose2d(2, 4, (2, 3), groups=2),
            cpp_constructor_args='torch::nn::ConvTranspose2dOptions(2, 4, {2, 3}).groups(2)',
            input_size=(1, 2, 4, 5),
            cudnn=True,
            check_with_long_tensor=True,
            with_tf32=True,
            tf32_precision=0.01,
            default_dtype=torch.double,
        ),
        dict(
            fullname='Conv2d_depthwise',
            constructor=lambda: nn.Conv2d(4, 4, (3, 3), groups=4),
            cpp_constructor_args='torch::nn::Conv2dOptions(4, 4, {3, 3}).groups(4)',
            input_size=(2, 4, 6, 6),
            with_tf32=True,
            tf32_precision=0.005,
            default_dtype=torch.double,
        ),
        dict(
            fullname='Conv2d_depthwise_with_multiplier',
            constructor=lambda: nn.Conv2d(4, 8, (3, 3), groups=4),
            cpp_constructor_args='torch::nn::Conv2dOptions(4, 8, {3, 3}).groups(4)',
            input_size=(2, 4, 6, 6),
            with_tf32=True,
            tf32_precision=0.005,
            default_dtype=torch.double,
        ),
        dict(
            fullname='Conv2d_depthwise_strided',
            constructor=lambda: nn.Conv2d(4, 4, (3, 3), stride=(2, 2), groups=4),
            cpp_constructor_args='torch::nn::Conv2dOptions(4, 4, {3, 3}).stride({2, 2}).groups(4)',
            input_size=(2, 4, 6, 6),
            with_tf32=True,
            tf32_precision=0.005,
            default_dtype=torch.double,
        ),
        dict(
            fullname='Conv2d_depthwise_padded',
            constructor=lambda: nn.Conv2d(4, 4, (3, 3), padding=(1, 1), groups=4),
            cpp_constructor_args='torch::nn::Conv2dOptions(4, 4, {3, 3}).padding({1, 1}).groups(4)',
            input_size=(2, 4, 6, 6),
            with_tf32=True,
            tf32_precision=0.005,
            default_dtype=torch.double,
        ),
        dict(
            fullname='Conv2d_depthwise_dilated',
            constructor=lambda: nn.Conv2d(4, 4, (2, 2), dilation=(2, 2), groups=4),
            cpp_constructor_args='torch::nn::Conv2dOptions(4, 4, {2, 2}).dilation({2, 2}).groups(4)',
            input_size=(2, 4, 5, 5),
            with_tf32=True,
            tf32_precision=0.005,
            default_dtype=torch.double,
        ),
        dict(
            module_name='Conv3d',
            constructor_args=(2, 3, (2, 3, 2)),
            cpp_constructor_args='torch::nn::Conv3dOptions(2, 3, {2, 3, 2})',
            input_size=(1, 2, 4, 5, 4),
            cudnn=True,
            check_with_long_tensor=True,
            with_tf32=True,
            tf32_precision=0.05,
            default_dtype=torch.double,
        ),
        dict(
            module_name='Conv3d',
            constructor_args=(2, 3, (2, 3, 4), 1, 0, 1, 1, False),
            cpp_constructor_args='''torch::nn::Conv3dOptions(2, 3, {2, 3, 4})
                                    .stride(1).padding(0).dilation(1).groups(1).bias(false)''',
            input_size=(1, 2, 3, 4, 5),
            cudnn=True,
            desc='no_bias',
            check_with_long_tensor=True,
            with_tf32=True,
            tf32_precision=0.05,
            default_dtype=torch.double,
        ),
        dict(
            module_name='Conv3d',
            constructor_args=(2, 3, (1, 1, 1), 1, 0, 1, 1, False),
            cpp_constructor_args='''torch::nn::Conv3dOptions(2, 3, {2, 3, 4})
                                    .stride(1).padding(0).dilation(1).groups(1).bias(false)''',
            input_size=(1, 2, 3, 4, 5),
            cudnn=True,
            desc='1x1x1_no_bias',
            check_with_long_tensor=False,
            with_tf32=True,
            tf32_precision=0.05,
            default_dtype=torch.double,
        ),
        dict(
            module_name='Conv3d',
            constructor_args=(3, 4, 2, 2),
            cpp_constructor_args='torch::nn::Conv3dOptions(3, 4, 2).stride(2)',
            input_size=(2, 3, 5, 5, 5),
            cudnn=True,
            desc='stride',
            check_with_long_tensor=True,
            with_tf32=True,
            tf32_precision=0.05,
            default_dtype=torch.double,
        ),
        dict(
            module_name='Conv3d',
            constructor_args=(3, 4, 2, 2, 1),
            cpp_constructor_args='torch::nn::Conv3dOptions(3, 4, 2).stride(2).padding(1)',
            input_size=(2, 3, 5, 5, 5),
            cudnn=True,
            desc='stride_padding',
            check_with_long_tensor=True,
            with_tf32=True,
            tf32_precision=0.05,
            default_dtype=torch.double,
        ),
        dict(
            module_name='Conv3d',
            constructor_args=(3, 4, (2, 3, 4)),
            cpp_constructor_args='torch::nn::Conv3dOptions(3, 4, {2, 3, 4})',
            input_size=(0, 3, 3, 4, 5),
            cudnn=True,
            check_with_long_tensor=True,
            desc='zero_batch',
            with_tf32=True,
        ),
        dict(
            fullname='Conv3d_groups',
            constructor=lambda: nn.Conv3d(2, 4, kernel_size=3, groups=2),
            cpp_constructor_args='torch::nn::Conv3dOptions(2, 4, 3).groups(2)',
            input_size=(1, 2, 4, 5, 4),
            cudnn=True,
            check_with_long_tensor=True,
            with_tf32=True,
            tf32_precision=0.005,
            default_dtype=torch.double,
        ),
        dict(
            fullname='Conv3d_dilated',
            constructor=lambda: nn.Conv3d(3, 4, kernel_size=2, dilation=2),
            cpp_constructor_args='torch::nn::Conv3dOptions(3, 4, 2).dilation(2)',
            input_size=(2, 3, 5, 5, 5),
            with_tf32=True,
            tf32_precision=0.05,
            default_dtype=torch.double,
        ),
        dict(
            fullname='Conv3d_dilated_strided',
            constructor=lambda: nn.Conv3d(3, 4, kernel_size=2, dilation=2, stride=2),
            cpp_constructor_args='torch::nn::Conv3dOptions(3, 4, 2).dilation(2).stride(2)',
            input_size=(2, 3, 5, 5, 5),
            with_tf32=True,
            tf32_precision=0.05,
            default_dtype=torch.double,
        ),
        dict(
            fullname='Conv3d_pad_valid',
            constructor=lambda: nn.Conv3d(3, 4, (2, 3, 4), padding="valid"),
            cpp_constructor_args='torch::nn::Conv3dOptions(3, 4, {2, 3, 4}).padding(torch::kValid)',
            input_size=(2, 3, 6, 5, 4),
            cudnn=True,
            with_tf32=True,
            tf32_precision=0.05,
            default_dtype=torch.double,
        ),
        dict(
            fullname='Conv3d_pad_same',
            constructor=lambda: nn.Conv3d(3, 4, (2, 3, 4), padding="same"),
            cpp_constructor_args='torch::nn::Conv3dOptions(3, 4, {2, 3, 4}).padding(torch::kSame)',
            input_size=(2, 3, 6, 5, 4),
            cudnn=True,
            with_tf32=True,
            tf32_precision=0.05,
            default_dtype=torch.double,
        ),
        dict(
            fullname='Conv3d_pad_same_dilated',
            constructor=lambda: nn.Conv3d(3, 4, (2, 3, 4), padding="same", dilation=2),
            cpp_constructor_args='torch::nn::Conv3dOptions(3, 4, {2, 3, 4}).padding(torch::kSame).dilation(2)',
            input_size=(2, 3, 6, 5, 4),
            cudnn=True,
            with_tf32=True,
            tf32_precision=0.05,
            default_dtype=torch.double,
        ),
        dict(
            module_name='ConvTranspose3d',
            constructor_args=(2, 3, (2, 3, 2)),
            cpp_constructor_args='torch::nn::ConvTranspose3dOptions(2, 3, {2, 3, 2})',
            cudnn=True,
            input_size=(1, 2, 4, 5, 4),
            with_tf32=True,
            tf32_precision=0.05,
            default_dtype=torch.double,
        ),
        dict(
            module_name='ConvTranspose3d',
            constructor_args=(2, 3, (2, 3, 2), 1, 0, 0, 1, True, (2, 2, 2)),
            cpp_constructor_args='''torch::nn::ConvTranspose3dOptions(2, 3, {2, 3, 2})
                                    .stride(1).padding(0).output_padding(0).groups(1).bias(true).dilation({2, 2, 2})''',
            cudnn=True,
            input_size=(1, 2, 4, 5, 4),
            desc='dilated',
            with_tf32=True,
            tf32_precision=0.05,
            default_dtype=torch.double,
        ),
        dict(
            module_name='ReplicationPad3d',
            constructor_args=((1, 2, 3, 3, 2, 1),),
            cpp_constructor_args='torch::nn::ReplicationPad3dOptions({1, 2, 3, 3, 2, 1})',
            input_size=(2, 3, 2, 2, 2),
            default_dtype=torch.double,
        ),
        dict(
            module_name='ReplicationPad3d',
            constructor_args=((1, 2, 3, 3, 2, 1),),
            cpp_constructor_args='torch::nn::ReplicationPad3dOptions({1, 2, 3, 3, 2, 1})',
            input_size=(3, 2, 2, 2),
            reference_fn=single_batch_reference_fn,
            desc='no_batch_dim',
            default_dtype=torch.double,
        ),
        dict(
            module_name='ReplicationPad3d',
            constructor_args=((1, 2, 3, 3, 2, 1),),
            cpp_constructor_args='torch::nn::ReplicationPad3dOptions({1, 2, 3, 3, 2, 1})',
            input_fn=lambda: torch.rand(2, 3, 2, 2, 2, dtype=torch.complex128, requires_grad=True),
            skip_half=True,
            desc='complex'
        ),
        dict(
            module_name='Embedding',
            constructor_args=(4, 3),
            cpp_constructor_args='torch::nn::EmbeddingOptions(4, 3)',
            input_fn=lambda: torch.empty(2, 3, dtype=torch.long).random_(4),
            check_gradgrad=False,
            default_dtype=torch.double,
            decorator=skipIfTorchDynamo("https://github.com/pytorch/pytorch/issues/117971")
        ),
        dict(
            module_name='Embedding',
            constructor_args=(4, 3),
            cpp_constructor_args='torch::nn::EmbeddingOptions(4, 3)',
            input_fn=lambda: torch.empty(1, 512, dtype=torch.long).random_(4).expand(7, 512),
            check_gradgrad=False,
            desc='discontiguous',
            default_dtype=torch.double,
            decorator=skipIfTorchDynamo("https://github.com/pytorch/pytorch/issues/117971")
        ),
        dict(
            module_name='EmbeddingBag',
            constructor_args=(4, 3),
            cpp_constructor_args='torch::nn::EmbeddingBagOptions(4, 3)',
            input_fn=lambda: torch.empty(2, 3, dtype=torch.long).random_(4),
            check_gradgrad=False,
            desc='mean',
            default_dtype=torch.double,
        ),
        dict(
            module_name='EmbeddingBag',
            constructor_args=(4, 3),
            cpp_constructor_args='torch::nn::EmbeddingBagOptions(4, 3)',
            input_fn=lambda: torch.empty(1, 512, dtype=torch.long).random_(4).expand(7, 512),
            check_gradgrad=False,
            desc='discontiguous',
            default_dtype=torch.double,
        ),
        dict(
            module_name='EmbeddingBag',
            constructor_args=(4, 3, None, 2., False, 'sum'),
            cpp_constructor_args='''torch::nn::EmbeddingBagOptions(4, 3)
                                    .max_norm(std::nullopt).norm_type(2.).scale_grad_by_freq(false).mode(torch::kSum)''',
            input_fn=lambda: torch.empty(2, 3, dtype=torch.long).random_(4),
            check_gradgrad=False,
            desc='sum',
            default_dtype=torch.double,
        ),
        dict(
            module_name='EmbeddingBag',
            constructor_args=(4, 3, None, 2., False, 'max'),
            cpp_constructor_args='''torch::nn::EmbeddingBagOptions(4, 3)
                                    .max_norm(std::nullopt).norm_type(2.).scale_grad_by_freq(false).mode(torch::kMax)''',
            input_fn=lambda: torch.empty(2, 3, dtype=torch.long).random_(4),
            check_gradgrad=False,
            desc='max',
            default_dtype=torch.double,
        ),
        dict(
            fullname='EmbeddingBag_mean_padding_idx',
            constructor=lambda: nn.EmbeddingBag(4, 3, padding_idx=1),
            cpp_constructor_args='torch::nn::EmbeddingBagOptions(4, 3).padding_idx(1)',
            input_fn=lambda: torch.stack([torch.randperm(3), torch.randperm(3)]),
            check_gradgrad=False,
            default_dtype=torch.double,
        ),
        dict(
            fullname='EmbeddingBag_sum_padding_idx',
            constructor=lambda: nn.EmbeddingBag(4, 3, None, 2., False, 'sum', padding_idx=1),
            cpp_constructor_args='''torch::nn::EmbeddingBagOptions(4, 3)
                                    .max_norm(std::nullopt).norm_type(2.).scale_grad_by_freq(false).mode(torch::kSum).padding_idx(1)''',
            input_fn=lambda: torch.stack([torch.randperm(3), torch.randperm(3)]),
            check_gradgrad=False,
            default_dtype=torch.double,
        ),
        dict(
            fullname='EmbeddingBag_max_padding_idx',
            constructor=lambda: nn.EmbeddingBag(4, 3, None, 2., False, 'max', padding_idx=1),
            cpp_constructor_args='''torch::nn::EmbeddingBagOptions(4, 3)
                                    .max_norm(std::nullopt).norm_type(2.).scale_grad_by_freq(false).mode(torch::kMax).padding_idx(1)''',
            input_fn=lambda: torch.stack([torch.randperm(3), torch.randperm(3)]),
            check_gradgrad=False,
            default_dtype=torch.double,
        ),
        dict(
            fullname='EmbeddingBag_sparse',
            constructor=lambda: nn.EmbeddingBag(4, 3, sparse=True, dtype=torch.double),
            cpp_constructor_args='''torch::nn::EmbeddingBagOptions(4, 3)
                                    .sparse(true)._weight(torch::rand({4, 3}).to(torch::kFloat64))''',
            input_fn=lambda: torch.randperm(2).repeat(1, 2),
            check_gradgrad=False,
            has_sparse_gradients=True,
        ),
        dict(
            constructor=lambda: nn.Embedding(4, 3, dtype=torch.double, sparse=True),
            cpp_constructor_args='torch::nn::EmbeddingOptions(4, 3).sparse(true)._weight(torch::rand({4, 3}).to(torch::kFloat64))',
            input_fn=lambda: torch.randperm(2).repeat(1, 2),
            fullname='Embedding_sparse',
            check_gradgrad=False,
            has_sparse_gradients=True,
        ),
        dict(
            module_name='PixelShuffle',
            constructor_args=(3,),
            cpp_constructor_args='torch::nn::PixelShuffleOptions(3)',
            input_size=(1, 9, 4, 4),
            default_dtype=torch.double,
        ),
        dict(
            module_name='PixelUnshuffle',
            constructor_args=(3,),
            cpp_constructor_args='torch::nn::PixelUnshuffleOptions(3)',
            input_size=(1, 1, 12, 12),
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=12, scale_factor=None, mode='nearest'),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::vector<int64_t>({12})).scale_factor(std::nullopt).mode(torch::kNearest)''',
            input_size=(1, 2, 4),
            fullname='interpolate_nearest_1d',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=12, scale_factor=None, mode='nearest'),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::vector<int64_t>({12})).scale_factor(std::nullopt).mode(torch::kNearest)''',
            input_size=(0, 2, 4),
            fullname='interpolate_nearest_1d_zero_dim',
            pickle=False,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=(12, ), scale_factor=None, mode='nearest'),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::vector<int64_t>({12})).scale_factor(std::nullopt).mode(torch::kNearest)''',
            input_size=(1, 2, 3),
            fullname='interpolate_nearest_tuple_1d',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=None, scale_factor=4., mode='nearest'),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::nullopt).scale_factor(std::vector<double>({4.})).mode(torch::kNearest)''',
            input_size=(1, 2, 4),
            fullname='interpolate_nearest_scale_1d',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=12, scale_factor=None, mode='linear', align_corners=False),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::vector<int64_t>({12}))
                                .scale_factor(std::nullopt)
                                .mode(torch::kLinear)
                                .align_corners(false)''',
            input_size=(1, 2, 4),
            fullname='interpolate_linear_1d',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=(4, ), scale_factor=None, mode='linear', align_corners=False),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::vector<int64_t>({4}))
                                .scale_factor(std::nullopt)
                                .mode(torch::kLinear)
                                .align_corners(false)''',
            input_size=(1, 2, 3),
            fullname='interpolate_linear_tuple_1d',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=None, scale_factor=4., mode='linear', align_corners=False),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::nullopt)
                                .scale_factor(std::vector<double>({4.}))
                                .mode(torch::kLinear)
                                .align_corners(false)''',
            input_size=(1, 2, 4),
            fullname='interpolate_linear_scale_1d',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=12, scale_factor=None, mode='linear', align_corners=False),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::vector<int64_t>({12}))
                                .scale_factor(std::nullopt)
                                .mode(torch::kLinear)
                                .align_corners(false)''',
            input_size=(0, 2, 4),
            fullname='interpolate_linear_1d_zero_dim',
            pickle=False,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=12, scale_factor=None, mode='linear', align_corners=True),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::vector<int64_t>({12}))
                                .scale_factor(std::nullopt)
                                .mode(torch::kLinear)
                                .align_corners(true)''',
            input_size=(1, 2, 4),
            fullname='interpolate_linear_1d_align_corners',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=None, scale_factor=4., mode='linear', align_corners=True),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::nullopt)
                                .scale_factor(std::vector<double>({4.}))
                                .mode(torch::kLinear)
                                .align_corners(true)''',
            input_size=(1, 2, 4),
            fullname='interpolate_linear_scale_1d_align_corners',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=2, scale_factor=None, mode='nearest'),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::vector<int64_t>({2, 2}))
                                .scale_factor(std::nullopt)
                                .mode(torch::kNearest)''',
            input_size=(1, 128, 1, 1),
            fullname='interpolate_nearest_2d_launch_configs',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=12, scale_factor=None, mode='nearest'),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::vector<int64_t>({12, 12}))
                                .scale_factor(std::nullopt)
                                .mode(torch::kNearest)''',
            input_size=(1, 2, 4, 4),
            fullname='interpolate_nearest_2d',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=(12, 16), scale_factor=None, mode='nearest'),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::vector<int64_t>({12, 16}))
                                .scale_factor(std::nullopt)
                                .mode(torch::kNearest)''',
            input_size=(1, 2, 3, 4),
            fullname='interpolate_nearest_tuple_2d',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=None, scale_factor=4., mode='nearest'),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::nullopt)
                                .scale_factor(std::vector<double>({4., 4.}))
                                .mode(torch::kNearest)''',
            input_size=(1, 2, 4, 4),
            fullname='interpolate_nearest_scale_2d',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=12, scale_factor=None, mode='nearest'),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::vector<int64_t>({12, 12}))
                                .scale_factor(std::nullopt)
                                .mode(torch::kNearest)''',
            input_size=(0, 2, 4, 4),
            fullname='interpolate_nearest_2d_zero_dim',
            pickle=False,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=12, scale_factor=None, mode='bilinear', align_corners=False),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::vector<int64_t>({12, 12}))
                                .scale_factor(std::nullopt)
                                .mode(torch::kBilinear)
                                .align_corners(false)''',
            input_size=(1, 2, 4, 4),
            fullname='interpolate_bilinear_2d',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=12, scale_factor=None, mode='bilinear', align_corners=False),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::vector<int64_t>({12, 12}))
                                .scale_factor(std::nullopt)
                                .mode(torch::kBilinear)
                                .align_corners(false)''',
            input_size=(0, 2, 4, 4),
            fullname='interpolate_bilinear_2d_zero_dim',
            pickle=False,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=(4, 6), scale_factor=None,
                                        mode='bilinear', align_corners=False),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::vector<int64_t>({4, 6}))
                                .scale_factor(std::nullopt)
                                .mode(torch::kBilinear)
                                .align_corners(false)''',
            input_size=(1, 2, 2, 3),
            fullname='interpolate_bilinear_tuple_2d',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=None, scale_factor=4.,
                                        mode='bilinear', align_corners=False),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::nullopt)
                                .scale_factor(std::vector<double>({4., 4.}))
                                .mode(torch::kBilinear)
                                .align_corners(false)''',
            input_size=(1, 2, 4, 4),
            fullname='interpolate_bilinear_scale_2d',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=None, scale_factor=(2., 2.),
                                        mode='bilinear', align_corners=False),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::nullopt)
                                .scale_factor(std::vector<double>({2., 2.}))
                                .mode(torch::kBilinear)
                                .align_corners(false)''',
            input_size=(1, 2, 4, 4),
            fullname='interpolate_bilinear_scale_tuple_shared_2d',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=None, scale_factor=(2., 1.),
                                        mode='bilinear', align_corners=False),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::nullopt)
                                .scale_factor(std::vector<double>({2., 1.}))
                                .mode(torch::kBilinear)
                                .align_corners(false)''',
            input_size=(1, 2, 4, 4),
            fullname='interpolate_bilinear_scale_tuple_skewed_2d',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=(4, 6), scale_factor=None, mode='bilinear', align_corners=True),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::vector<int64_t>({4, 6}))
                                .scale_factor(std::nullopt)
                                .mode(torch::kBilinear)
                                .align_corners(true)''',
            input_size=(1, 2, 4, 4),
            fullname='interpolate_bilinear_tuple_2d_align_corners',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=None, scale_factor=(2., 1.),
                                        mode='bilinear', align_corners=True),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::nullopt)
                                .scale_factor(std::vector<double>({2., 1.}))
                                .mode(torch::kBilinear)
                                .align_corners(true)''',
            input_size=(1, 2, 4, 4),
            fullname='interpolate_bilinear_scale_tuple_skewed_2d_align_corners',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=12, scale_factor=None, mode='bicubic', align_corners=False),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::vector<int64_t>({12, 12}))
                                .scale_factor(std::nullopt)
                                .mode(torch::kBicubic)
                                .align_corners(false)''',
            input_size=(1, 2, 4, 4),
            fullname='interpolate_bicubic_2d',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=12, scale_factor=None, mode='bicubic', align_corners=False),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::vector<int64_t>({12, 12}))
                                .scale_factor(std::nullopt)
                                .mode(torch::kBicubic)
                                .align_corners(false)''',
            input_size=(0, 2, 4, 4),
            fullname='interpolate_bicubic_2d_zero_dim',
            pickle=False,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=(4, 6), scale_factor=None,
                                        mode='bicubic', align_corners=False),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::vector<int64_t>({4, 6}))
                                .scale_factor(std::nullopt)
                                .mode(torch::kBicubic)
                                .align_corners(false)''',
            input_size=(1, 2, 2, 3),
            fullname='interpolate_bicubic_tuple_2d',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=None, scale_factor=4., mode='bicubic', align_corners=False),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::nullopt)
                                .scale_factor(std::vector<double>({4., 4.}))
                                .mode(torch::kBicubic)
                                .align_corners(false)''',
            input_size=(1, 2, 4, 4),
            fullname='interpolate_bicubic_scale_2d',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=None, scale_factor=(2., 2.),
                                        mode='bicubic', align_corners=False),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::nullopt)
                                .scale_factor(std::vector<double>({2., 2.}))
                                .mode(torch::kBicubic)
                                .align_corners(false)''',
            input_size=(1, 2, 4, 4),
            fullname='interpolate_bicubic_scale_tuple_shared_2d',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=None, scale_factor=(2., 1.),
                                        mode='bicubic', align_corners=False),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::nullopt)
                                .scale_factor(std::vector<double>({2., 1.}))
                                .mode(torch::kBicubic)
                                .align_corners(false)''',
            input_size=(1, 2, 4, 4),
            fullname='interpolate_bicubic_scale_tuple_skewed_2d',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=(4, 6), scale_factor=None, mode='bicubic', align_corners=True),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::vector<int64_t>({4, 6}))
                                .scale_factor(std::nullopt)
                                .mode(torch::kBicubic)
                                .align_corners(true)''',
            input_size=(1, 2, 4, 4),
            fullname='interpolate_bicubic_tuple_2d_align_corners',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=None, scale_factor=(2., 1.),
                                        mode='bicubic', align_corners=True),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::nullopt)
                                .scale_factor(std::vector<double>({2., 1.}))
                                .mode(torch::kBicubic)
                                .align_corners(true)''',
            input_size=(1, 2, 4, 4),
            fullname='interpolate_bicubic_scale_tuple_skewed_2d_align_corners',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=12, scale_factor=None, mode='nearest'),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::vector<int64_t>({12, 12, 12}))
                                .scale_factor(std::nullopt)
                                .mode(torch::kNearest)''',
            input_size=(1, 2, 4, 4, 4),
            fullname='interpolate_nearest_3d',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=12, scale_factor=None, mode='nearest'),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::vector<int64_t>({12, 12, 12}))
                                .scale_factor(std::nullopt)
                                .mode(torch::kNearest)''',
            input_size=(0, 2, 4, 4, 4),
            fullname='interpolate_nearest_3d_zero_dim',
            pickle=False,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=(12, 16, 16), scale_factor=None, mode='nearest'),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::vector<int64_t>({12, 16, 16}))
                                .scale_factor(std::nullopt)
                                .mode(torch::kNearest)''',
            input_size=(1, 2, 3, 4, 4),
            fullname='interpolate_nearest_tuple_3d',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=None, scale_factor=4., mode='nearest'),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::nullopt)
                                .scale_factor(std::vector<double>({4., 4., 4.}))
                                .mode(torch::kNearest)''',
            input_size=(1, 2, 4, 4, 4),
            fullname='interpolate_nearest_scale_3d',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=12, scale_factor=None, mode='trilinear', align_corners=False),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::vector<int64_t>({12, 12, 12}))
                                .scale_factor(std::nullopt)
                                .mode(torch::kTrilinear)
                                .align_corners(false)''',
            input_size=(1, 2, 4, 4, 4),
            fullname='interpolate_trilinear_3d',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=12, scale_factor=None, mode='trilinear', align_corners=False),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::vector<int64_t>({12, 12, 12}))
                                .scale_factor(std::nullopt)
                                .mode(torch::kTrilinear)
                                .align_corners(false)''',
            input_size=(0, 2, 4, 4, 4),
            fullname='interpolate_trilinear_3d_zero_dim',
            pickle=False,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=(4, 6, 6),
                                        scale_factor=None, mode='trilinear', align_corners=False),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::vector<int64_t>({4, 6, 6}))
                                .scale_factor(std::nullopt)
                                .mode(torch::kTrilinear)
                                .align_corners(false)''',
            input_size=(1, 2, 2, 3, 3),
            fullname='interpolate_trilinear_tuple_3d',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=None, scale_factor=3., mode='trilinear', align_corners=False),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::nullopt)
                                .scale_factor(std::vector<double>({3., 3., 3.}))
                                .mode(torch::kTrilinear)
                                .align_corners(false)''',
            input_size=(1, 2, 3, 4, 5),
            fullname='interpolate_trilinear_scale_3d',
            # See https://github.com/pytorch/pytorch/issues/5006
            precision=3e-4,
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=(4, 6, 6), scale_factor=None,
                                        mode='trilinear', align_corners=True),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::vector<int64_t>({4, 6, 6}))
                                .scale_factor(std::nullopt)
                                .mode(torch::kTrilinear)
                                .align_corners(true)''',
            input_size=(1, 2, 2, 3, 3),
            fullname='interpolate_trilinear_tuple_3d_align_corners',
            pickle=False,
            default_dtype=torch.double
        ),
        dict(
            constructor=wrap_functional(F.interpolate, size=None, scale_factor=3., mode='trilinear', align_corners=True),
            cpp_options_args='''F::InterpolateFuncOptions()
                                .size(std::nullopt)
                                .scale_factor(std::vector<double>({3., 3., 3.}))
                                .mode(torch::kTrilinear)
                                .align_corners(true)''',
            input_size=(1, 2, 3, 4, 4),
            fullname='interpolate_trilinear_scale_3d_align_corners',
            # See https://github.com/pytorch/pytorch/issues/5006
            precision=3e-4,
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.softmax, dim=-1),
            cpp_options_args='F::SoftmaxFuncOptions(-1)',
            input_size=(2, 128),  # trigger the last-dim algo in CUDA
            fullname='softmax_lastdim',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.softmax, dim=1, dtype=torch.float64),
            cpp_options_args='F::SoftmaxFuncOptions(1).dtype(torch::kFloat64)',
            input_size=(2, 128),
            fullname='softmax_lastdim_dtype',
            pickle=False,
            test_cuda=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.softmax, dim=1),
            cpp_options_args='F::SoftmaxFuncOptions(1)',
            input_size=(2, 128, 2, 2),  # trigger special case of spatial CUDA algo
            fullname='softmax_spatial_special',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.softmax, dim=1),
            cpp_options_args='F::SoftmaxFuncOptions(1)',
            input_size=(2, 2, 4, 4),  # regular spatial algorithm
            fullname='softmax_spatial',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.softmax, dim=1, dtype=torch.float64),
            cpp_options_args='F::SoftmaxFuncOptions(1).dtype(torch::kFloat64)',
            input_size=(2, 2, 4, 4),  # regular spatial algorithm
            fullname='softmax_spatial_dtype',
            pickle=False,
            test_cuda=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.softmax, dim=0),
            cpp_options_args='F::SoftmaxFuncOptions(0)',
            input_size=(2, 3, 4, 5),
            fullname='softmax_functional_dim0',
            test_cuda=False,
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.softmax, dim=3),
            cpp_options_args='F::SoftmaxFuncOptions(3)',
            input_size=(2, 3, 4, 5),
            fullname='softmax_functional_dim3',
            test_cuda=False,
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.softmax, dim=-1),
            cpp_options_args='F::SoftmaxFuncOptions(-1)',
            input_size=(),
            fullname='softmax_functional_scalar',
            test_cuda=False,
            pickle=False,
        ),
        dict(
            constructor=wrap_functional(F.log_softmax, dim=-1),
            cpp_options_args='F::LogSoftmaxFuncOptions(-1)',
            input_size=(2, 128),  # trigger the last-dim algo in CUDA
            fullname='log_softmax_lastdim',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.log_softmax, dim=1),
            cpp_options_args='F::LogSoftmaxFuncOptions(1)',
            input_size=(2, 128, 2, 2),  # trigger special case of spatial CUDA algo
            fullname='log_softmax_spatial_special',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.log_softmax, dim=1),
            cpp_options_args='F::LogSoftmaxFuncOptions(1)',
            input_size=(2, 2, 4, 4),  # regular spatial algorithm
            fullname='log_softmax_spatial',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.log_softmax, dim=0),
            cpp_options_args='F::LogSoftmaxFuncOptions(0)',
            input_size=(2, 3, 4, 5),
            fullname='log_softmax_dim0',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.log_softmax, dim=3),
            cpp_options_args='F::LogSoftmaxFuncOptions(3)',
            input_size=(2, 3, 4, 5),
            fullname='log_softmax_dim3',
            pickle=False,
            default_dtype=torch.double,
        ),
        dict(
            constructor=wrap_functional(F.log_softmax, dim=0),
            cpp_options_args='F::LogSoftmaxFuncOptions(0)',
            input_size=(),
            fullname='log_softmax_scalar',
            pickle=False,
        ),
        dict(
            fullname='Unfold',
            constructor=lambda: nn.Unfold((2, 2), (1, 1), (0, 0), (1, 1)),
            cpp_constructor_args='torch::nn::UnfoldOptions({2, 2}).dilation({1, 1}).padding({0, 0}).stride({1, 1})',
            input_size=(2, 4, 3, 3),
            check_gradgrad=False,
            test_cuda=True,
            default_dtype=torch.double,
        ),
        dict(
            fullname='Fold',
            constructor=lambda: nn.Fold((3, 3), (2, 2), (1, 1), (0, 0), (1, 1)),
            cpp_constructor_args='torch::nn::FoldOptions({3, 3}, {2, 2}).dilation({1, 1}).padding({0, 0}).stride({1, 1})',
            input_size=(2, 16, 4),
            check_gradgrad=False,
            test_cuda=True,
            default_dtype=torch.double,
        ),
        dict(
            fullname='Fold_no_batch_dim_input',
            constructor=lambda: nn.Fold((3, 3), (2, 2), (1, 1), (0, 0), (1, 1)),
            cpp_constructor_args='torch::nn::FoldOptions({3, 3}, {2, 2}).dilation({1, 1}).padding({0, 0}).stride({1, 1})',
            input_size=(16, 4),
            check_gradgrad=False,
            ref=single_batch_reference_fn,
            test_cuda=True,
            default_dtype=torch.double,
        ),
        dict(
            fullname='Unfold_int_input',
            constructor=lambda: nn.Unfold(2, 1, 0, 1),
            cpp_constructor_args='torch::nn::UnfoldOptions(2).dilation(1).padding(0).stride(1)',
            input_size=(2, 4, 3, 3),
            check_gradgrad=False,
            test_cuda=True,
            default_dtype=torch.double,
        ),
        dict(
            fullname='Fold_int_input',
            constructor=lambda: nn.Fold(3, 2, 1, 0, 1),
            cpp_constructor_args='torch::nn::FoldOptions(3, 2).dilation(1).padding(0).stride(1)',
            input_size=(2, 16, 4),
            check_gradgrad=False,
            test_cuda=True,
            default_dtype=torch.double,
        ),
        dict(
            fullname='Fold_no_batch_dim_int_input',
            constructor=lambda: nn.Fold(3, 2, 1, 0, 1),
            cpp_constructor_args='torch::nn::FoldOptions(3, 2).dilation(1).padding(0).stride(1)',
            input_size=(16, 4),
            ref=single_batch_reference_fn,
            check_gradgrad=False,
            test_cuda=True,
            default_dtype=torch.double,
        ),
        dict(
            module_name='RReLU',
            constructor_args=(0.1, 0.9),
            cpp_constructor_args='torch::nn::RReLUOptions().lower(0.1).upper(0.9)',
            input_size=(),
            desc='with_up_down_scalar',
            test_cuda=False,
            default_dtype=torch.double,
        ),
        dict(
            module_name='PairwiseDistance',
            input_fn=lambda: (torch.randn(10, 8), torch.randn(10, 8)),
            default_dtype=torch.double,
        ),
        dict(
            module_name='PairwiseDistance',
            input_fn=lambda: (torch.randn(10, 1), torch.randn(10, 8)),
            desc='broadcast_lhs',
            default_dtype=torch.double,
        ),
        dict(
            module_name='PairwiseDistance',
            input_fn=lambda: (torch.randn(10, 8), torch.randn(1, 8)),
            desc='broadcast_rhs',
            default_dtype=torch.double,
        ),
        dict(
            module_name='PairwiseDistance',
            constructor_args=(1.5, 1e-05, True),
            cpp_constructor_args='torch::nn::PairwiseDistanceOptions().p(1.5).eps(1e-05).keepdim(true)',
            input_fn=lambda: (torch.randn(10, 8), torch.randn(10, 8)),
            desc='with_non_default_args',
            default_dtype=torch.double,
        ),
        dict(
            module_name='PairwiseDistance',
            input_fn=lambda: (torch.randn(8), torch.randn(8)),
            reference_fn=single_batch_reference_fn,
            desc='no_batch_dim',
            default_dtype=torch.double,
        ),
        dict(
            module_name='TransformerEncoderLayer',
            constructor_args=(4, 2, 16, 0.0),
            cpp_constructor_args='''torch::nn::TransformerEncoderLayerOptions(4, 2)
                                    .dim_feedforward(16)
                                    .dropout(0.0)''',
            input_size=(2, 3, 4),
            desc='relu_activation',
            with_tf32=True,
            tf32_precision=0.1,
            # TODO(#50743): figure out the error
            # RuntimeError: The size of tensor a (6) must match the size of tensor b (4)
            # at non-singleton dimension 2
            check_batched_grad=False,
            check_gradgrad=False,
            default_dtype=torch.double,
        ),
        dict(
            module_name='TransformerEncoderLayer',
            constructor_args=(4, 2, 8, 0.0, F.gelu),
            cpp_constructor_args='''torch::nn::TransformerEncoderLayerOptions(4, 2)
                                    .dim_feedforward(8)
                                    .dropout(0.0)
                                    .activation(torch::kGELU)''',
            input_size=(2, 3, 4),
            check_gradgrad=False,
            desc='gelu_activation',
            with_tf32=True,
            tf32_precision=0.08 if SM90OrLater else 0.05,
            default_dtype=torch.double,
        ),
        dict(
            module_name='TransformerDecoderLayer',
            constructor_args=(4, 2, 8, 0.0),
            cpp_constructor_args='''torch::nn::TransformerDecoderLayerOptions(4, 2)
                                    .dim_feedforward(8)
                                    .dropout(0.0)''',
            input_fn=lambda: (torch.rand(3, 3, 4), torch.rand(2, 3, 4)),
            check_gradgrad=False,
            desc='relu_activation',
            with_tf32=True,
            tf32_precision=0.05,
            default_dtype=torch.double,
        ),
        dict(
            module_name='TransformerDecoderLayer',
            constructor_args=(4, 2, 8, 0.0, F.gelu),
            cpp_constructor_args='''torch::nn::TransformerDecoderLayerOptions(4, 2)
                                    .dim_feedforward(8)
                                    .dropout(0.0)
                                    .activation(torch::kGELU)''',
            input_fn=lambda: (torch.rand(3, 3, 4), torch.rand(2, 3, 4)),
            check_gradgrad=False,
            desc='gelu_activation',
            with_tf32=True,
            tf32_precision=0.05,
            default_dtype=torch.double,
        ),
        dict(
            module_name='Transformer',
            constructor_args=(4, 2, 2, 2, 8, 0.0, F.relu),
            cpp_constructor_args='''torch::nn::TransformerOptions()
                                    .d_model(4)
                                    .nhead(2)
                                    .num_encoder_layers(2)
                                    .num_decoder_layers(2)
                                    .dim_feedforward(8)
                                    .dropout(0.0)
                                    .activation(torch::kReLU)''',
            input_fn=lambda: (torch.rand(3, 3, 4), torch.rand(2, 3, 4), torch.rand(3, 3)),
            check_gradgrad=False,
            desc='multilayer_coder',
            with_tf32=True,
            tf32_precision=0.05 if SM90OrLater else 0.03,
            default_dtype=torch.double,
        ),
        dict(
            module_name='Linear',
            constructor_args=(3, 5),
            cpp_constructor_args='torch::nn::LinearOptions(3, 5)',
            input_fn=lambda: torch.rand(3),
            reference_fn=lambda i, p, _: torch.mm(i.view(1, -1), p[0].t()).view(-1) + p[1],
            desc="no_batch_dim",
            with_tf32=True,
            tf32_precision=0.005,
            default_dtype=torch.double,
        ),
        dict(
            module_name='Flatten',
            cpp_constructor_args='torch::nn::FlattenOptions().start_dim(-3).end_dim(-1)',
            constructor_args=(-3, -1),
            input_size=(3, 4, 5),
            reference_fn=single_batch_reference_fn,
            desc="no_batch_dim",
            default_dtype=torch.double,
        ),
        dict(
            module_name='Unflatten',
            cpp_constructor_args='torch::nn::UnflattenOptions(-2, {2, 2})',
            constructor_args=(-2, torch.Size([2, 2])),
            input_size=(3, 4, 5),
            reference_fn=single_batch_reference_fn,
            desc="no_batch_dim",
            default_dtype=torch.double,
        ),
        dict(
            module_name='LayerNorm',
            constructor_args=([56, 56, 56], 1e-5, False),
            cpp_constructor_args='torch::nn::LayerNormOptions({56, 56, 56}).eps(1e-5).elementwise_affine(false)',
            input_size=(4, 56, 56, 56),
            cudnn=True,
            check_eval=True,
            gradcheck_fast_mode=True,
            check_half=True,
            desc='3d_no_affine_large_feature',
        ),
    ]

    # add conv padding mode tests:
    for padding_mode, cpp_padding_mode in zip(
            ['reflect', 'circular', 'replicate', 'zeros'],
            ['torch::kReflect', 'torch::kCircular', 'torch::kReplicate', 'torch::kZeros'], strict=True):
        # conv signature:
        #     in_channels, out_channels, kernel_size, stride=1,
        #     padding=0, dilation=1, groups=1,
        #     bias=True, padding_mode='zeros'
        for d in (1, 2, 3):
            if d == 3 and padding_mode == 'reflect':
                # FIXME: remove after implementing reflection pad 3d
                #        https://github.com/pytorch/pytorch/issues/27655
                continue
            padding = tuple(range(1, d + 1))
            cpp_padding = '{' + ', '.join(map(str, padding)) + '}'
            input_size = (2, 2) + (4,) * d
            output_size = (2, 3) + tuple(p + 1 for p in padding)  # simplified from `(4 + 2 * p - 3) // 2 + 1`
            new_module_tests.append(
                dict(
                    module_name=f'Conv{d}d',
                    constructor_args=(2, 3, 3, 2, padding, 1, 1, True, padding_mode),
                    cpp_constructor_args=f'''torch::nn::Conv{d}dOptions(2, 3, 3)
                                            .stride(2)
                                            .padding({cpp_padding})
                                            .dilation(1)
                                            .groups(1)
                                            .bias(true)
                                            .padding_mode({cpp_padding_mode})''',
                    input_size=input_size,
                    output_size=output_size,
                    cudnn=True,
                    desc=f'{padding_mode}_stride2_pad2',
                    with_tf32=True,
                    tf32_precision=0.05,
                    default_dtype=torch.double,
                ),
            )

    # Check that non linear activations work with no batch dimensions
    non_linear_activations_no_batch = [
        'ELU', 'Hardshrink', 'Hardsigmoid', 'Hardtanh', 'Hardswish', 'LeakyReLU',
        'LogSigmoid', 'PReLU', 'ReLU', 'ReLU6', 'RReLU', 'SELU', 'CELU', 'GELU', 'GLU',
        'Sigmoid', 'SiLU', 'Mish', 'Softplus', 'Softshrink', 'Softsign', 'Tanh',
        'Tanhshrink', 'Threshold'
    ]
    non_linear_activations_extra_info: dict[str, dict] = {
        'CELU': {'constructor_args': (2.,), 'default_dtype': torch.double},
        'Threshold': {'constructor_args': (2., 1.)},
        'Hardsigmoid': {'check_gradgrad': False, 'check_jit': False, 'default_dtype': torch.double},
        'Hardswish': {'check_gradgrad': False, 'check_jit': False, 'default_dtype': torch.double},
        # For RRelu, test that compare CPU and GPU results fail because RNG
        # is different between CPU and GPU
        'RReLU': {'test_cuda': False, 'default_dtype': torch.double},
        'ELU': {'default_dtype': torch.double},
        'GELU': {'default_dtype': torch.double},
        'GLU': {'default_dtype': torch.double},
        'Hardshrink': {'default_dtype': torch.double},
        'Hardtanh': {'default_dtype': torch.double},
        'LeakyReLU': {'default_dtype': torch.double},
        'LogSigmoid': {'default_dtype': torch.double},
        'Mish': {'default_dtype': torch.double},
        'PReLU': {'default_dtype': torch.double},
        'ReLU6': {'default_dtype': torch.double},
        'ReLU': {'default_dtype': torch.double},
        'SELU': {'default_dtype': torch.double},
        'SiLU': {'default_dtype': torch.double},
        'Sigmoid': {'default_dtype': torch.double},
        'Softplus': {'default_dtype': torch.double},
        'Softshrink': {'default_dtype': torch.double},
        'Softsign': {'default_dtype': torch.double},
        'Tanh': {'default_dtype': torch.double},
        'Tanhshrink': {'default_dtype': torch.double},
    }
    for non_linear_activation in non_linear_activations_no_batch:
        activation_test_info = dict(
            module_name=non_linear_activation,
            input_size=(4,),
            reference_fn=single_batch_reference_fn,
            desc='no_batch_dim',
            test_cpp_api_parity=False,
        )
        extra_info = non_linear_activations_extra_info.get(non_linear_activation, {})
        activation_test_info.update(extra_info)
        new_module_tests.append(activation_test_info)


    return new_module_tests