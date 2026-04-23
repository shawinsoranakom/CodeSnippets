def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.copied_files = []
        self.symlinked_files = []
        self.unmodified_files = []
        self.post_processed_files = []
        self.skipped_files = []
        self.deleted_files = []
        self.storage = staticfiles_storage
        self.style = no_style()