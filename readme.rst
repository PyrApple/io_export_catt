CATT-Acoustic Export Utility
============================

Catt-Acousitic model export Addon for Blender 2.75

Using exported model in CATT-Acoustic
-------------------------------------

Remove default audiance plane in CATT, else model import will raise an error because first face in model is not necessarily horizontal (while audiance plane should be)

TODO
----

- Impl.: Only the first 15 caracters of material name are taken into acount in CATT
- Conflict with 3D printing toolbox add-on (when not active at blender start) make catt addon disapear.
