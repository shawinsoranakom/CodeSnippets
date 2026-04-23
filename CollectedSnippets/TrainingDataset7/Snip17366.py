def __setitem__(self, *args, **kwargs):
                nonlocal setitem_count
                setitem_count += 1
                super().__setitem__(*args, **kwargs)