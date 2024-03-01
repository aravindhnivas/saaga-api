"""
For extracting metadata (dipole moments, rotational constants,
and partition function) from .int, .var, and .qpart files, respectively.
"""

from decimal import Decimal
import re
from io import BufferedReader


def read_intfile(filein: BufferedReader):
    """Reads in .int file and returns diple moments"""

    file = [ln.decode().strip() for ln in filein.readlines()]
    # print(f"Reading dipole moments from .int file: {file[0]}\n")

    mu_a, mu_b, mu_c = None, None, None

    for line in file[2:]:

        if not line:
            break

        split_line = line.split()
        label, value = split_line[0], split_line[1]

        if "1" in label:
            mu_a = value
        elif "2" in label:
            mu_b = value
        elif "3" in label:
            mu_c = value
    print(f"Read dipole moments: {mu_a=}\n{mu_b=}\n{mu_c=}\n")
    return mu_a, mu_b, mu_c


def read_varfile(filein: BufferedReader):
    """Reads in .var file and returns rotational constants"""

    filein = [ln.decode().strip() for ln in filein.readlines()]
    # print(f"Reading rotational constants from .var file: {filein[0]}\n")
    a_const, b_const, c_const = None, None, None

    for line in filein:

        if not line:
            continue

        if "/A" in line:
            a_const = float(line.split()[1])
        if "/B" in line:
            b_const = float(line.split()[1])
        if "/C" in line:
            c_const = float(line.split()[1])

    print(
        f"Read rotaional constants: a_const: {a_const}\nb_const: {b_const}\nc_const: {c_const}"
    )
    return a_const, b_const, c_const


def read_qpartfile(filein: BufferedReader):
    """Reads in .qpart file and returns partition function"""
    file = filein.readlines()
    partition_dict = {}
    for line in file:
        if "#" in line.decode():
            continue
        split_line = line.split()
        partition_dict[split_line[0].decode()] = split_line[1].decode()

    pattern = re.compile(r"300\.?0*")
    if not any(pattern.fullmatch(key) for key in partition_dict):
        raise ValueError("Partition function does not contain 300.000 K")
    return partition_dict
