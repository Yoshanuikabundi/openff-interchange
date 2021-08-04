import mdtraj as md
import pytest
from openff.toolkit.topology import Molecule
from openff.toolkit.typing.engines.smirnoff import ForceField
from simtk.openmm import app

from openff.interchange.components.interchange import Interchange
from openff.interchange.components.mdtraj import (
    _get_num_h_bonds,
    _iterate_pairs,
    _iterate_propers,
    _OFFBioTop,
    _store_bond_partners,
)
from openff.interchange.drivers import get_openmm_energies
from openff.interchange.utils import get_test_file_path


@pytest.mark.slow()
def test_residues():
    pdb = app.PDBFile(get_test_file_path("ALA_GLY/ALA_GLY.pdb"))
    traj = md.load(get_test_file_path("ALA_GLY/ALA_GLY.pdb"))
    mol = Molecule(get_test_file_path("ALA_GLY/ALA_GLY.sdf"), file_format="sdf")

    top = _OFFBioTop.from_openmm(pdb.topology, unique_molecules=[mol])
    top.mdtop = traj.top

    assert top.n_topology_atoms == 29
    assert top.mdtop.n_residues == 4
    assert [r.name for r in top.mdtop.residues] == ["ACE", "ALA", "GLY", "NME"]

    ff = ForceField("openff-1.3.0.offxml")
    off_sys = Interchange.from_smirnoff(ff, top)

    # Assign positions and box vectors in order to run MM
    off_sys.positions = pdb.positions
    off_sys.box = [4.8, 4.8, 4.8]

    # Just ensure that a single-point energy can be obtained without error
    get_openmm_energies(off_sys)

    assert len(top.mdtop.select("resname ALA")) == 10
    assert [*off_sys.topology.mdtop.residues][-1].n_atoms == 6


def test_iterate_pairs():
    mol = Molecule.from_smiles("C1#CC#CC#C1")

    top = mol.to_topology()

    mdtop = md.Topology.from_openmm(top.to_openmm())

    _store_bond_partners(mdtop)
    pairs = {
        tuple(sorted((atom1.index, atom2.index)))
        for atom1, atom2 in _iterate_pairs(mdtop)
    }
    assert len(pairs) == 3
    assert len([*_iterate_propers(mdtop)]) > len(pairs)


def test_iterate_pairs_benzene():
    """Check that bonds in rings are not double-counted with _iterate_pairs.
    This should be fixed by using Topology.nth_degree_neighbors directly"""
    benzene = Molecule.from_smiles("c1ccccc1")
    mdtop = md.Topology.from_openmm(benzene.to_topology().to_openmm())

    _store_bond_partners(mdtop)

    assert len({*_iterate_pairs(mdtop)}) == 21


def test_get_num_h_bonds():
    mol = Molecule.from_smiles("CCO")
    top = mol.to_topology()
    mdtop = md.Topology.from_openmm(top.to_openmm())
    assert _get_num_h_bonds(mdtop) == 6
