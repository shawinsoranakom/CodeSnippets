def check_do_nothing(sender, **kwargs):
            obj = kwargs["instance"]
            obj.donothing_set.update(donothing=replacement_r)