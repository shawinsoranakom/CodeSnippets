def create_hero(hero: Hero, session: Session = Depends(get_session)) -> Hero:
    session.add(hero)
    session.commit()
    session.refresh(hero)
    return hero