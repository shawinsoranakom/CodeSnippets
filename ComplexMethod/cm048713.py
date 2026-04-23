def templ(env, code, name=None, country='', **kwargs):
    country_code = country or code.split('_')[0] if country is not None else None
    country = country_code and env.ref(f"base.{country_code}", raise_if_not_found=False)
    country_name = f"{get_flag(country.code)} {country.name}" if country else ''
    return {
        'name': country_name and (f"{country_name} - {name}" if name else country_name) or name,
        'country_id': country and country.id,
        'country_code': country and country.code,
        **kwargs,
    }