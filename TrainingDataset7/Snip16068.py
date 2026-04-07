def today_callable_q():
    return models.Q(last_action__gte=datetime.datetime.today())