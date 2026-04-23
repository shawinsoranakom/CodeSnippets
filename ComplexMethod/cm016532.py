def create_cond_with_same_area_if_none(conds, c):
    if 'area' not in c:
        return

    def area_inside(a, area_cmp):
        a = add_area_dims(a, len(area_cmp) // 2)
        area_cmp = add_area_dims(area_cmp, len(a) // 2)

        a_l = len(a) // 2
        area_cmp_l = len(area_cmp) // 2
        for i in range(min(a_l, area_cmp_l)):
            if a[a_l + i] < area_cmp[area_cmp_l + i]:
                return False
        for i in range(min(a_l, area_cmp_l)):
            if (a[i] + a[a_l + i]) > (area_cmp[i] + area_cmp[area_cmp_l + i]):
                return False
        return True

    c_area = c['area']
    smallest = None
    for x in conds:
        if 'area' in x:
            a = x['area']
            if area_inside(c_area, a):
                if smallest is None:
                    smallest = x
                elif 'area' not in smallest:
                    smallest = x
                else:
                    if math.prod(smallest['area'][:len(smallest['area']) // 2]) > math.prod(a[:len(a) // 2]):
                        smallest = x
        else:
            if smallest is None:
                smallest = x
    if smallest is None:
        return
    if 'area' in smallest:
        if smallest['area'] == c_area:
            return

    out = c.copy()
    out['model_conds'] = smallest['model_conds'].copy() #TODO: which fields should be copied?
    conds += [out]