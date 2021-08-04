"""Assorted utilities."""
import pathlib
from collections import OrderedDict

from openff.toolkit.typing.engines.smirnoff import ForceField
from pkg_resources import resource_filename
from simtk import openmm
from simtk import unit as omm_unit


def pint_to_simtk(quantity):
    """Convert a pint Quantity to an OpenMM unit."""
    # TODO: Move these hacks into openff-units
    if str(quantity.units) in ["kilojoule / mole", "kJ / mol"]:
        return quantity.m * omm_unit.kilojoule_per_mole
    if str(quantity.units) == "1 / nm":
        return quantity.m / omm_unit.nanometer
    if str(quantity.units) == "1 / Å":
        return quantity.m / omm_unit.angstrom
    if str(quantity.units) in [
        "kilojoule * nanometer ** 6 / mole",
        "nanometer ** 6 * kilojoule / mole",
    ]:
        return quantity.m * omm_unit.nanometer ** 6 / omm_unit.kilojoule_per_mole
    if str(quantity.units) == "kJ * Å ** 6 / mol":
        return quantity.m * omm_unit.angstrom ** 6 / omm_unit.kilojoule_per_mole
    if str(quantity.units) == "erg / mol":
        return quantity.m * omm_unit.erg / omm_unit.mole
    if str(quantity.units) == "erg * Å ** 6 / mol":
        return quantity.m * omm_unit.erg * omm_unit.angstrom ** 6 / omm_unit.mole
    else:
        raise NotImplementedError(f"caught units {str(quantity.units)}")


def _unwrap_list_of_pint_quantities(quantities):
    assert {val.units for val in quantities} == {quantities[0].units}
    parsed_unit = quantities[0].units
    vals = [val.magnitude for val in quantities]
    return vals * parsed_unit


def get_test_file_path(test_file) -> str:
    """Given a filename in the collection of data files, return its full path."""
    dir_path = resource_filename("openff.interchange", "tests/files/")
    test_file_path = pathlib.Path(dir_path).joinpath(test_file)

    if test_file_path.is_file():
        return test_file_path.as_posix()
    else:
        raise FileNotFoundError(f"could not file file {test_file} in path {dir_path}")


def get_test_files_dir_path(dirname):
    """Given a directory with a collection of test data files, return its full path."""
    dir_path = resource_filename("openff.interchange", "tests/files/")
    test_dir = pathlib.Path(dir_path).joinpath(dirname)

    if test_dir.is_dir():
        return test_dir.as_posix()
    else:
        raise NotADirectoryError(
            f"Provided directory {dirname} doesn't exist in {dir_path}"
        )


def get_nonbonded_force_from_openmm_system(omm_system):
    """Get a single NonbondedForce object with an OpenMM System."""
    for force in omm_system.getForces():
        if type(force) == openmm.NonbondedForce:
            return force


def get_partial_charges_from_openmm_system(omm_system):
    """Get partial charges from an OpenMM interchange as a unit.Quantity array."""
    # TODO: deal with virtual sites
    n_particles = omm_system.getNumParticles()
    force = get_nonbonded_force_from_openmm_system(omm_system)
    # TODO: don't assume the partial charge will always be parameter 0
    # partial_charges = [simtk_to_pint(force.getParticleParameters(idx)[0]) for idx in range(n_particles)]
    partial_charges = [
        force.getParticleParameters(idx)[0] / omm_unit.elementary_charge
        for idx in range(n_particles)
    ]

    return partial_charges


def _check_forcefield_dict(forcefield):
    """Ensure an OpenFF ForceField is represented as a dict and convert it if it is not."""
    if isinstance(forcefield, ForceField):
        return forcefield._to_smirnoff_data()
    elif isinstance(forcefield, OrderedDict):
        return forcefield


def compare_forcefields(ff1, ff2):
    """Compare dict representations of OpenFF ForceField objects for equality."""
    ff1 = _check_forcefield_dict(ff1)
    ff2 = _check_forcefield_dict(ff2)

    assert ff1 == ff2
