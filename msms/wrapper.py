from collections import namedtuple
from io import StringIO
import os.path
import subprocess
from tempfile import TemporaryDirectory

import numpy as np

SurfaceParams = namedtuple("SurfaceParams", "probe_radius density hdensity")

class MsmsOutput:

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
        self.log_lines = log_lines
        self.vertices = vertices
        self.faces = faces
        return

    @classmethod
    def from_files(cls, log_file, vert_file, face_file):
        vert_data = np.loadtxt(vert_file, skiprows=3, dtype=cls.VERT_DTYPES)
        face_data = np.loadtxt(face_file, skiprows=3, dtype=cls.FACE_DTYPES)
        log_lines = log_file.readlines()
        return cls(
            log_lines = log_lines,
            vertices = vert_data,
            faces = face_data,
        )

    def params(self):
        line_it = iter(self.log_lines)
        for line in line_it:
            if line.startswith("PARAM"):
                elems = line.split()
                params = SurfaceParams(float(elems[2]), float(elems[4]), float(elems[6]))
                return params


def run_msms(xyz, radii, *args, **kwargs):
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
        formatted_kwargs = []
        for k, v in kwargs.items():
            formatted_kwargs.extend(["-"+str(k), str(v)])
        call = ["msms", "-if", xyzr_fname, "-of", out_basename, *args] + formatted_kwargs
        process = subprocess.run(call, cwd=tmp, capture_output=True)
        if process.returncode != 0:
            raise RuntimeError(f"msms returned nonzero return. stdout: {process.stdout}, stderr: {process.stderr}")
        log_filehandle = StringIO(process.stdout.decode("utf-8"))
        with (
            open(out_basename + ".vert") as vert_file,
            open(out_basename + ".face") as face_file
        ):
            return MsmsOutput.from_files(log_file=log_filehandle, vert_file=vert_file, face_file=face_file)
