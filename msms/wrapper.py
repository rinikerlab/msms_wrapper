from collections import namedtuple
from io import StringIO
import os.path
import subprocess
from tempfile import TemporaryDirectory
from scipy.spatial import KDTree

import numpy as np
import shutil

SurfaceParams = namedtuple("SurfaceParams", "probe_radius density hdensity")
SizeDescriptors = namedtuple('SizeDescriptors', 'ses sas volume')

class MsmsOutput:
    """
    Class to hold the output of an Msms run

    Attributes:
    * log_lines: list of str with the lines of the standard output
    * vertices: structured np.ndarray with the data from the .vert output file
    * faces: structured np.ndarray with the data from the .face output file

    Notes:
    * currently assumes that -all_components is not set!
    """

    FACE_DTYPES = [
        ('i', 'int'),
        ('j', 'int'),
        ('k', 'int'),
        ('face_type', 'int'),
        ('face_number', 'int'),
    ]

    VERT_DTYPES = [
        ('x', 'float'),
        ('y', 'float'),
        ('z', 'float'),
        ('nx', 'float'),
        ('ny', 'float'),
        ('nz', 'float'),
        ('vertex_type', 'int'),
        ('closest_sphere', 'int'),
        ('face_type', 'int'),
    ]

    AREA_DTYPES = [
        ("sphere", int),
        ("ses_0", float),
        ("sas_0", float),
    ]

    def __init__(self, log_lines, vertices, faces, areas=None):
        """Create from lines of a logfile, and structured arrays."""
        self.log_lines = log_lines
        self.vertices = vertices
        self.faces = faces
        self.areas = areas
        return

    @classmethod
    def from_files(cls, log_file, vert_file, face_file, area_file=None):
        """Create from file objects."""
        vert_data = np.loadtxt(vert_file, skiprows=3, dtype=cls.VERT_DTYPES)
        face_data = np.loadtxt(face_file, skiprows=3, dtype=cls.FACE_DTYPES)
        if area_file:
            area_data = np.loadtxt(area_file, skiprows=1, dtype=cls.AREA_DTYPES)
        else:
            area_data = None
        log_lines = log_file.readlines()
        return cls(
            log_lines = log_lines,
            vertices = vert_data,
            faces = face_data,
            areas = area_data
        )

    def params(self) -> SurfaceParams:
        """Extract parameters of the msms run."""
        line_it = iter(self.log_lines)
        for line in line_it:
            if line.startswith("PARAM"):
                elems = line.split()
                params = SurfaceParams(float(elems[2]), float(elems[4]), float(elems[6]))
                return params

    def extract_ses_sas_vol(self) -> SizeDescriptors:
        """Return the analytical SES and SAS, and the numerical volume."""
        lines = iter(self.log_lines)
        ses = None
        sas = None
        volume = None
        for line in lines:
            if line.startswith("ANALYTICAL SURFACE AREA :"):
                next(lines)
                entries = next(lines).split()
                ses = float(entries[5])
                sas = float(entries[6])
            elif line.strip().startswith("Total ses_volume:"):
                entries = line.split()
                volume = float(entries[2])
        if ses is None or sas is None:
            raise ValueError("Could not find analytical surface area in the msms output.")
        if volume is None:
            raise ValueError("Could not find numerical SES volume in the msms output.")
        return SizeDescriptors(ses, sas, volume)

    def get_vertex_positions(self):
        """return vertex positions (x, y, z) as regular numpy array."""
        return np.stack([self.vertices['x'], self.vertices['y'], self.vertices['z']], axis=-1)

    def get_vertex_normals(self):
        """Return the vertex normals as regular numpy array."""
        return np.stack([self.vertices['nx'], self.vertices['ny'], self.vertices['nz']], axis=-1)

    def get_face_indices(self, zero_indexed=True):
        """Return indices of triangles in self.faces, optionally zero-indexed."""
        out = np.stack([self.faces['i'], self.faces['j'], self.faces['k']], axis=-1)
        if zero_indexed:
            out -= 1
        return out

    def get_ses_per_sphere(self):
        return self.areas["ses_0"]

    def get_sas_per_sphere(self):
        return self.areas["sas_0"]



def run_msms(xyz, radii, *args, compute_area=False, temp_dir=None, check_small_atoms=False, **kwargs) -> MsmsOutput:
    """Run msms with the given args and kwargs, return an MsmsOutput.

    * compute_area: run msms with -af and pass the area file to MsmsOutput.
    * temp_dir: parent directory of the temporary directory for the msms run.
    * check_small_atoms: if True, remove atoms from the structure if they are
      inside their nearest-neighbor atom.
    * args will be given to the subprocess.run as strings.
    * kwargs will be formatted, i.e., when calling with density=2.0, will add
      ['-density', '2.0'] to the argument list.
    """
    xyz = np.asarray(xyz)
    radii = np.asarray(radii)
    if check_small_atoms:
        return _run_msms_check_small_atoms(xyz, radii, *args, compute_area=compute_area, temp_dir=temp_dir, **kwargs)
    if len(xyz.shape) != 2 or xyz.shape[1] != 3:
        raise ValueError("xyz must have shape (N, 3)")
    if radii.shape != (xyz.shape[0],):
        raise ValueError(f"radii must have shape ({xyz.shape[0]},), not {radii.shape}")
    with TemporaryDirectory(dir=temp_dir) as tmp:
        xyzr_fname = os.path.join(tmp, "input.xyzr")
        out_basename = os.path.join(tmp, "out")
        xyzr = np.hstack([xyz, radii[:, np.newaxis]])
        np.savetxt(xyzr_fname, xyzr)
        extra_args = [str(arg) for arg in args]
        for k, v in kwargs.items():
            extra_args.extend(["-"+str(k), str(v)])
        if compute_area:
            extra_args.extend(["-af", out_basename])
        call = ["msms", "-if", xyzr_fname, "-of", out_basename] + extra_args
        process = subprocess.run(call, cwd=tmp, capture_output=True)
        if process.returncode != 0:
            raise RuntimeError(f"msms returned nonzero return. stdout: {process.stdout}, stderr: {process.stderr}")
        log_filehandle = StringIO(process.stdout.decode("utf-8"))
        if compute_area:
            with open(out_basename + ".vert") as vert_file, \
                 open(out_basename + ".face") as face_file, \
                 open(out_basename + ".area") as area_file:
                return MsmsOutput.from_files(log_file=log_filehandle, vert_file=vert_file, face_file=face_file, area_file=area_file)
        else:
            with open(out_basename + ".vert") as vert_file, \
                 open(out_basename + ".face") as face_file:
                return MsmsOutput.from_files(log_file=log_filehandle, vert_file=vert_file, face_file=face_file)

def _run_msms_check_small_atoms(xyz, radii, *args, **kwargs):
    """Fix cases where a few atoms are completely inside other atoms.

    Note: This only checks if an atom is inside its nearest neighbor! It might
    fail when radii are too uneven.
    """
    tree = KDTree(xyz)
    dist, ind = tree.query(xyz, k=2)
    nbr_dist = dist[:, 1]
    nbr_radii = radii[ind[:, 1]]
    good_atoms = radii > (nbr_radii - nbr_dist)
    return run_msms(xyz[good_atoms], radii[good_atoms], *args, **kwargs)

def help() -> str:
    """Obtain the msms help message."""
    call = ["msms", "-h"]
    process = subprocess.run(call, capture_output=True)
    if process.returncode != 0:
        raise RuntimeError(f"msms -h returned nonzero return. stdout: {process.stdout}, stderr: {process.stderr}")
    return process.stderr.decode("utf-8")


def msms_available() -> bool:
    return shutil.which("msms") is not None
