# Minimal Python wrapper for the msms program
`msms` is a command-line program developed by Dr. Michel F. Sanner, that computes triangulated solvent-excluded surfaces. It is available from https://ccsb.scripps.edu/msms/.

If you have `msms` installed on your computer, you can use this package as a Python interface for its basic functionality.

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
`run_msms` returns a `MsmsOutput` object.
The triangulated surfaces are available as structured numpy arrays through the `.vertices` and `.faces` attributes of the `MsmsOutput`.
Additionally, there are convenience functions: `get_vertex_positions`, `get_vertex_normals`, and `get_face_indices`, to obtain the most important data as numpy arrays.

## Further examples
See `examples.ipynb`
