from collections import namedtuple
from io import StringIO
import os.path
import subprocess
from tempfile import TemporaryDirectory

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

    def __init__(self, log_lines, vertices, faces):
        """Create from lines of a logfile, and structured arrays."""
        self.log_lines = log_lines
        self.vertices = vertices
        self.faces = faces
        return

    @classmethod
    def from_files(cls, log_file, vert_file, face_file):
        """Create from file objects."""
        vert_data = np.loadtxt(vert_file, skiprows=3, dtype=cls.VERT_DTYPES)
        face_data = np.loadtxt(face_file, skiprows=3, dtype=cls.FACE_DTYPES)
        log_lines = log_file.readlines()
        return cls(
            log_lines = log_lines,
            vertices = vert_data,
            faces = face_data,
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


def run_msms(xyz, radii, *args, **kwargs) -> MsmsOutput:
    """Run msms with the given args and kwargs, return an MsmsOutput.

    * args will be given to the subprocess.run as strings.
    * kwargs will be formatted, i.e., when calling with density=2.0, will add
      ['-density', '2.0'] to the argument list.
    """
    xyz = np.asarray(xyz)
    radii = np.asarray(radii)
    if len(xyz.shape) != 2 or xyz.shape[1] != 3:
        raise ValueError("xyz must have shape (N, 3)")
    if radii.shape != (xyz.shape[0],):
        raise ValueError(f"radii must have shape ({xyz.shape[0]},), not {radii.shape}")
    with TemporaryDirectory() as tmp:
        xyzr_fname = os.path.join(tmp, "input.xyzr")
        out_basename = os.path.join(tmp, "out")
        xyzr = np.hstack([xyz, radii[:, np.newaxis]])
        np.savetxt(xyzr_fname, xyzr)
        extra_args = [str(arg) for arg in args]
        for k, v in kwargs.items():
            extra_args.extend(["-"+str(k), str(v)])
        call = ["msms", "-if", xyzr_fname, "-of", out_basename] + extra_args
        process = subprocess.run(call, cwd=tmp, capture_output=True)
        if process.returncode != 0:
            raise RuntimeError(f"msms returned nonzero return. stdout: {process.stdout}, stderr: {process.stderr}")
        log_filehandle = StringIO(process.stdout.decode("utf-8"))
        with open(out_basename + ".vert") as vert_file, \
             open(out_basename + ".face") as face_file:
            return MsmsOutput.from_files(log_file=log_filehandle, vert_file=vert_file, face_file=face_file)


def help() -> str:
    """Obtain the msms help message."""
    call = ["msms", "-h"]
    process = subprocess.run(call, capture_output=True)
    if process.returncode != 0:
        raise RuntimeError(f"msms -h returned nonzero return. stdout: {process.stdout}, stderr: {process.stderr}")
    return process.stderr.decode("utf-8")


def msms_available() -> bool:
    return shutil.which("msms") is not None
