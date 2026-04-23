def __init__(self, box_embeddings=None, box_mask=None, box_labels=None):
        """Initialize the Prompt object."""
        # Check for null prompt
        # Check for null prompt
        if box_embeddings is None:
            self.box_embeddings = None
            self.box_labels = None
            self.box_mask = None
            return

        # Get sequence length, batch size, and device
        box_seq_len = box_embeddings.shape[0]
        bs = box_embeddings.shape[1]
        device = box_embeddings.device

        # Initialize labels and attention mask if not provided
        if box_labels is None:
            box_labels = torch.ones(box_seq_len, bs, device=device, dtype=torch.long)
        if box_mask is None:
            box_mask = torch.zeros(bs, box_seq_len, device=device, dtype=torch.bool)

        # Dimension checks
        assert list(box_embeddings.shape[:2]) == [box_seq_len, bs], (
            f"Wrong dimension for box embeddings. Expected [{box_seq_len}, {bs}, *] got {box_embeddings.shape}"
        )
        assert box_embeddings.shape[-1] == 4, (
            f"Expected box embeddings to have 4 coordinates, got {box_embeddings.shape[-1]}"
        )
        assert list(box_mask.shape) == [bs, box_seq_len], (
            f"Wrong dimension for box mask. Expected [{bs}, {box_seq_len}] got {box_mask.shape}"
        )
        assert list(box_labels.shape) == [box_seq_len, bs], (
            f"Wrong dimension for box labels. Expected [{box_seq_len}, {bs}] got {box_labels.shape}"
        )

        # Device checks
        assert box_embeddings.device == device, (
            f"Expected box embeddings to be on device {device}, got {box_embeddings.device}"
        )
        assert box_mask.device == device, f"Expected box mask to be on device {device}, got {box_mask.device}"
        assert box_labels.device == device, f"Expected box labels to be on device {device}, got {box_labels.device}"

        self.box_embeddings = box_embeddings
        self.box_mask = box_mask
        self.box_labels = box_labels