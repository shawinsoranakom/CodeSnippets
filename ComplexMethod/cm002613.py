def _process_flash_attention_kwargs(
    query_length: int,
    key_length: int,
    is_causal: bool,
    dropout: float = 0.0,
    softmax_scale: float | None = None,
    sliding_window: int | None = None,
    use_top_left_mask: bool = False,
    softcap: float | None = None,
    deterministic: bool | None = None,
    s_aux: torch.Tensor | None = None,
    max_seqlen_q: int | torch.IntTensor | None = None,
    max_seqlen_k: int | torch.IntTensor | None = None,
    supports_mapping: dict[str, bool] | None = None,
    **kwargs,
):
    """
    Returns a set of kwargs that are passed down to the according flash attention function based on
    requested features and whether it is supported - depends on the version and kernel implementation
    which is dynamically configured at `lazy_import_flash_attention`. The (un)supported features can be
    inspected in `supports_mapping`, see `_lazy_define_process_function` for more details.

    Args:
        query_length (`int`):
            Length of the query states
        key_length (`int`):
            Length of the key states
        is_causal (`bool`):
            Whether we perform causal (decoder) attention or full attention.
        dropout (`float`):
            Attention dropout.
        softmax_scale (`float`, *optional*):
            The scaling of QK^T before applying softmax. Default to `1 / sqrt(head_dim)`.
        sliding_window (`int`, *optional*):
            The size of the sliding window, i.e. we look at a max of `sliding_window` tokens back.
        use_top_left_mask (`bool`):
            Deprecated behavior of older versions of flash attention requiring different masking.
        softcap (`float`, *optional*):
            Softcap for the attention logits, used e.g. in gemma2.
        deterministic (`bool`, *optional*):
            Determines if the deterministic option introduced in flash_attn>=2.4.1 is enabled.
        s_aux (`torch.Tensor`, *optional*):
            Attention sink auxiliary that adds a `bias` to the attention calculation via an additional head.
        max_seqlen_q (`Union[int, torch.IntTensor]`, *optional*):
            The maximum sequence length in the query tensor during a varlen forward.
        max_seqlen_k (`Union[int, torch.IntTensor]`, *optional*):
            The maximum sequence length in the key/value tensor during a varlen forward.
    Return:
        flash_kwargs (`dict`):
            A dict of kwargs that are requested and supported.
    """
    flash_kwargs = {
        "causal": is_causal and not (use_top_left_mask and query_length == 1),
        "softmax_scale": softmax_scale,
    }

    if supports_mapping["dropout_p"]:
        flash_kwargs["dropout_p"] = dropout

    if supports_mapping["window_size"] and sliding_window is not None and key_length > sliding_window:
        # The flash attention API sets inclusive boundaries, i.e. (4, 0) would take 4 tokens to the left
        # and the current token for a total size of 5. However, we usually define our window sizes by
        # their total window size (when causal). Encoder models as of now seldom use SWA and when they
        # do, they must align with this symmetric logic, i.e. for a total of `2*sliding_window + 1`.
        flash_kwargs["window_size"] = (sliding_window - 1, sliding_window - 1)

    if supports_mapping["deterministic"]:
        flash_kwargs["deterministic"] = (
            deterministic if deterministic is not None else os.getenv("FLASH_ATTENTION_DETERMINISTIC", "0") == "1"
        )

    if supports_mapping["softcap"] and softcap is not None:
        flash_kwargs["softcap"] = softcap

    if ((legacy_sink_param := supports_mapping["s_aux"]) or supports_mapping["learnable_sink"]) and s_aux is not None:
        if legacy_sink_param:
            flash_kwargs["s_aux"] = s_aux  # e.g. FA3 (vllm)
        else:
            flash_kwargs["learnable_sink"] = s_aux  # FA4

    # There is a limitation of the flash attention API, as the function `flash_attn_varlen_func`
    # may require `max_length_q`, `max_length_k` to be passed as `int` and not `torch.Tensor`.
    #
    # You can either set
    #   - Env: `TORCHDYNAMO_CAPTURE_SCALAR_OUTPUTS=1`
    #   - Before compiling: `torch._dynamo.config.capture_scalar_outputs = True`
    # to allow torch compile to handle scalar outputs in those cases.
    same_max_seqlen = max_seqlen_q is max_seqlen_k  # to avoid 2x device syncs
    if supports_mapping["max_seqlen_q"] and max_seqlen_q is not None:
        if not isinstance(max_seqlen_q, int) and is_tracing(max_seqlen_q):
            max_seqlen_q = max_seqlen_q.item()
        flash_kwargs["max_seqlen_q"] = max_seqlen_q

    if supports_mapping["max_seqlen_k"] and max_seqlen_k is not None:
        if same_max_seqlen and flash_kwargs["max_seqlen_q"] is not None:
            max_seqlen_k = flash_kwargs["max_seqlen_q"]
        elif not isinstance(max_seqlen_k, int) and is_tracing(max_seqlen_k):
            max_seqlen_k = max_seqlen_k.item()
        flash_kwargs["max_seqlen_k"] = max_seqlen_k

    return flash_kwargs