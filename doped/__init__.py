"""
``doped`` is a python package for managing solid-state defect calculations, with
functionality to generate defect structures and relevant competing phases (for
chemical potentials), interface with ShakeNBreak
(https://shakenbreak.readthedocs.io) for defect structure-searching (see
https://www.nature.com/articles/s41524-023-00973-1), write VASP input files for
defect supercell calculations, and automatically parse and analyse the results.
"""

import contextlib
import inspect
import multiprocessing
import warnings
from importlib.metadata import PackageNotFoundError, version

from packaging.version import parse
from pymatgen.io.vasp.inputs import UnknownPotcarWarning
from pymatgen.io.vasp.sets import BadInputSetWarning


def _check_pmg_compatibility():
    try:
        v_pmg_def = version("pymatgen-analysis-defects")
    except PackageNotFoundError:
        v_pmg_def = False

    try:
        v_pmg = version("pymatgen")
    except Exception:
        v_pmg = False

    if not v_pmg_def:
        raise TypeError(
            "You do not have the `pymatgen-analysis-defects` package installed, which is required by "
            "`doped`. Please install `pymatgen-analysis-defects` (with `pip install "
            "pymatgen-analysis-defects`) and restart the kernel."
        )

    if parse(v_pmg) < parse("2022.7.25"):
        raise TypeError(
            f"You have the version {v_pmg} of `pymatgen` installed, which is incompatible with `doped`. "
            f"Please update (with `pip install --upgrade pymatgen`) and restart the kernel."
        )


_check_pmg_compatibility()


def _ignore_pmg_warnings():
    # globally ignore these POTCAR warnings; `message` only needs to match start of message
    warnings.filterwarnings("ignore", category=UnknownPotcarWarning)
    warnings.filterwarnings("ignore", category=BadInputSetWarning)
    warnings.filterwarnings("ignore", message="No POTCAR file with matching TITEL fields")
    warnings.filterwarnings("ignore", message="Ignoring unknown variable type")

    # Ignore because comment after 'ALGO = Normal' causes this unnecessary warning:
    warnings.filterwarnings("ignore", message="Hybrid functionals only support")

    warnings.filterwarnings("ignore", message="Use get_magnetic_symmetry()")
    warnings.filterwarnings("ignore", message="Use of properties is now deprecated")

    # avoid warning about selective_dynamics properties (can happen if user explicitly set "T T T" (or
    # otherwise) for the bulk):
    warnings.filterwarnings("ignore", message="Not all sites have property")

    # ignore warning about structure charge that appears when getting Vasprun.as_dict():
    warnings.filterwarnings("ignore", message="Structure charge")


_ignore_pmg_warnings()


def _doped_obj_properties_methods(obj):
    """
    Return a tuple of the attributes & properties and methods of a given
    object.

    Used in the ``__repr__()`` methods of ``doped`` objects.
    """
    attrs = {k for k in vars(obj) if not k.startswith("_")}
    methods = set()
    for k in dir(obj):
        with contextlib.suppress(Exception):
            if callable(getattr(obj, k)) and not k.startswith("_"):
                methods.add(k)
    properties = {name for name, value in inspect.getmembers(type(obj)) if isinstance(value, property)}
    return attrs | properties, methods


def get_mp_context():
    """
    Get a multiprocessing context that is compatible with the current OS.
    """
    try:
        return multiprocessing.get_context("forkserver")
    except ValueError:  # forkserver not available on Windows OS
        return multiprocessing.get_context("spawn")
