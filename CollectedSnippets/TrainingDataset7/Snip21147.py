def log_pre_delete(sender, **kwargs):
            post_delete_order.append((sender, kwargs["instance"].pk))