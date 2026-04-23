def center_of_mass(particles: list[Particle]) -> Coord3D:
    """
    Input Parameters
    ----------------
    particles: list(Particle):
    A list of particles where each particle is a tuple with it's (x, y, z) position and
    it's mass.

    Returns
    -------
    Coord3D:
    A tuple with the coordinates of the center of mass (Xcm, Ycm, Zcm) rounded to two
    decimal places.

    Examples
    --------
    >>> center_of_mass([
    ...     Particle(1.5, 4, 3.4, 4),
    ...     Particle(5, 6.8, 7, 8.1),
    ...     Particle(9.4, 10.1, 11.6, 12)
    ... ])
    Coord3D(x=6.61, y=7.98, z=8.69)

    >>> center_of_mass([
    ...     Particle(1, 2, 3, 4),
    ...     Particle(5, 6, 7, 8),
    ...     Particle(9, 10, 11, 12)
    ... ])
    Coord3D(x=6.33, y=7.33, z=8.33)

    >>> center_of_mass([
    ...     Particle(1, 2, 3, -4),
    ...     Particle(5, 6, 7, 8),
    ...     Particle(9, 10, 11, 12)
    ... ])
    Traceback (most recent call last):
        ...
    ValueError: Mass of all particles must be greater than 0

    >>> center_of_mass([
    ...     Particle(1, 2, 3, 0),
    ...     Particle(5, 6, 7, 8),
    ...     Particle(9, 10, 11, 12)
    ... ])
    Traceback (most recent call last):
        ...
    ValueError: Mass of all particles must be greater than 0

    >>> center_of_mass([])
    Traceback (most recent call last):
        ...
    ValueError: No particles provided
    """
    if not particles:
        raise ValueError("No particles provided")

    if any(particle.mass <= 0 for particle in particles):
        raise ValueError("Mass of all particles must be greater than 0")

    total_mass = sum(particle.mass for particle in particles)

    center_of_mass_x = round(
        sum(particle.x * particle.mass for particle in particles) / total_mass, 2
    )
    center_of_mass_y = round(
        sum(particle.y * particle.mass for particle in particles) / total_mass, 2
    )
    center_of_mass_z = round(
        sum(particle.z * particle.mass for particle in particles) / total_mass, 2
    )
    return Coord3D(center_of_mass_x, center_of_mass_y, center_of_mass_z)