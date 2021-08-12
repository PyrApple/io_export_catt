# CATT-Acoustic Export Utility

Catt-Acousitic model export Addon for Blender


## How to use

- All enabled (not excluded from view layer) collections will be included in the export
- Add * to object name end to flag its faces for auto edge scattering
- Add * to object name end to flag its faces for auto edge scattering


## Using exported model in CATT-Acoustic

Remove default audiance plane in CATT, else model import will raise an error because first face in model is not necessarily horizontal (while audiance plane should be)


## Flat faces

Catt only accepts flat faces. Either use the triangulate option of the add-on to fix non-flat faces upon export or blender internal tools:

    - in edit mode, select all, go to the mesh menu, then clean up and make planar faces (after switching to face select mode).
    – and/or look in to properties menu (N key) in edit mode, and use "mesh analysis" > type: distortion, it will let you see what's wrong
    - and/or use the 3d print add-on, set a low angle into "distortion" and press the button: it will let you see what's wrong


## Export from Catt to Blender

### export WRL from CATT

CATT WRL export parameters (in doubt, disable all options):
    - disable triangulation, to avoid degenerated faces creation
    - disabled show edges (same)

### Fix CATT exported WRL file after import in Blender

changes to operate on imported WRL in blender to get a model with the same coordinates as Catt's original:

- rotate the whole scene (rooms, listeners, sources) around center along Z axis of 180 degrees
- rotate each individual listener along local center in local coordinate system:
    - rot x -90 ( RXX -90 )
    - rot z 90  ( RZZ 90 )


note: the tricky thing about solving that problem is that it seems to come from the WRL export/import process. A scene created in Blender, and exported to CATT seems to have correct transform (for all room, listeners, sources). The re-export from CATT -> WRL -> Blender however creates this weird change.


## Todo

- Impl.: Only the first 15 caracters of material name are taken into acount in CATT
