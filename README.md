# Minimal Python wrapper for the msms program
This is a Python wrapper for the `msms` command-line program developed by Dr. Michel F. Sanner. It can be used to compute triangulated solvent-excluded surfaces of molecules, as well as their solvent-accessible surface (SAS), solvent excluded surface (SES), and molecular volume.

Note: While this wrapper is under the MIT licence, `msms` is not. This is an independent project and not affiliated to the `msms` program. You can obtain `msms` from https://ccsb.scripps.edu/msms/. For more information about the algorithm, see:

Sanner, M. F., Olson A.J. & Spehner, J.-C. (1996). Reduced Surface: An Efficient Way to Compute Molecular Surfaces. Biopolymers 38:305-320.

# Functionality
If you have `msms` installed on your computer, you can use this package as a Python interface for its basic functionality. Supported features include
* obtaining a triangulated surface based on atomic positions and radii.
* obtain the SAS, SES, and molecular volume.

# Installation
The wrapper is a single file (`msms/wrapper.py`), which you can copy into one of your folders/projects. Alternatively, download this repository and run `pip install .`.

# Usage
## Use `msms` to compute the surface area of a unit sphere.
* The SES and SAS are analyical.
* The volume is numerical. In the case of a single sphere, it is always too small, but converges with high density.

```
xyz = [[0., 0., 0.]]
radii = [1.]
print('expected SES', 4*np.pi)
print('expected SAS', 4*np.pi * 2.5**2) # 2.5 = radius + probe_radius
print('expected volume', 4/3*np.pi)
msms.run_msms(xyz, radii, density=2).extract_ses_sas_vol()
```
Output:
```
expected SES 12.566370614359172
expected SAS 78.53981633974483
expected volume 4.1887902047863905

SizeDescriptors(ses=12.566, sas=78.54, volume=3.082)
```
## Triangulated surfaces
* `run_msms` returns a `MsmsOutput` object.
* Convenience functions: `get_vertex_positions`, `get_vertex_normals`, and `get_face_indices` return numpy arrays with the most important data.
* structured numpy arrays: the `.vertices` and `.faces` attributes of `MsmsOutput` contain structured numpy arrays that contain basically all information in the `.vert` and `.face` files.

## Further examples
See `examples.ipynb`
