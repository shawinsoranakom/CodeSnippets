def __init__(self, model, load_device, offload_device, size=0, weight_inplace_update=False):
        self.size = size
        self.model = model
        if not hasattr(self.model, 'device'):
            logging.debug("Model doesn't have a device attribute.")
            self.model.device = offload_device
        elif self.model.device is None:
            self.model.device = offload_device

        self.patches = {}
        self.backup = {}
        self.backup_buffers = {}
        self.object_patches = {}
        self.object_patches_backup = {}
        self.weight_wrapper_patches = {}
        self.model_options = {"transformer_options":{}}
        self.load_device = load_device
        self.offload_device = offload_device
        self.weight_inplace_update = weight_inplace_update
        self.force_cast_weights = False
        self.patches_uuid = uuid.uuid4()
        self.parent = None
        self.pinned = set()

        self.attachments: dict[str] = {}
        self.additional_models: dict[str, list[ModelPatcher]] = {}
        self.callbacks: dict[str, dict[str, list[Callable]]] = CallbacksMP.init_callbacks()
        self.wrappers: dict[str, dict[str, list[Callable]]] = WrappersMP.init_wrappers()

        self.is_injected = False
        self.skip_injection = False
        self.injections: dict[str, list[PatcherInjection]] = {}

        self.hook_patches: dict[comfy.hooks._HookRef] = {}
        self.hook_patches_backup: dict[comfy.hooks._HookRef] = None
        self.hook_backup: dict[str, tuple[torch.Tensor, torch.device]] = {}
        self.cached_hook_patches: dict[comfy.hooks.HookGroup, dict[str, torch.Tensor]] = {}
        self.current_hooks: Optional[comfy.hooks.HookGroup] = None
        self.forced_hooks: Optional[comfy.hooks.HookGroup] = None  # NOTE: only used for CLIP at this time
        self.is_clip = False
        self.hook_mode = comfy.hooks.EnumHookMode.MaxSpeed

        self.cached_patcher_init: tuple[Callable, tuple] | None = None
        if not hasattr(self.model, 'model_loaded_weight_memory'):
            self.model.model_loaded_weight_memory = 0

        if not hasattr(self.model, 'lowvram_patch_counter'):
            self.model.lowvram_patch_counter = 0

        if not hasattr(self.model, 'model_lowvram'):
            self.model.model_lowvram = False

        if not hasattr(self.model, 'current_weight_patches_uuid'):
            self.model.current_weight_patches_uuid = None

        if not hasattr(self.model, 'model_offload_buffer_memory'):
            self.model.model_offload_buffer_memory = 0