def log_post_delete(sender, **kwargs):
            pre_delete_order.append((sender, kwargs["instance"].pk))