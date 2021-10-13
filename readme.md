# CATT-Acoustic Export Utility

Blender add-on to export scenes to CATT-Acoustic .GEO format


## How to use

Add objects to the scene, assign materials to these objects, convert those materials to CATT materials and press the export button. Only those objects in collections not excluded from the view layer will be included in the export. Upon export, all the objects concerned are merged, and a "remove duplicate vertices" operation is applied on the resulting mesh. The add-on only supports mesh export to .GEO: sources and receivers will not be taken into account.


## Export syntax

The exported .GEO file contains a list of objects faces (named "planes" in CATT) vertices (named "corners" in CATT) and materials.

### Material

format:
``abs material_name = <absorption_coefficients> L <scattering_coefficients> {rgb_color}``

example:
``abs Concrete = <1.0 2.0 3.0 4.0 5.0 6.0 : 7.0 8.0> L <10.0 11.0 12.0 13.0 14.0 15.0 : 16.0 17.0> {1 80 1}``

### Corner

format:
``corner_id xyz_coordinates``

example:
``1 -4.50 -5.87 8.00``

### Plane

format:
``[ plane_id plane_name / plane_corners_ids / material_name ]``

example:
``[ 10 OuterShell-Room-9 / 62 57 60 65 37 66 / Concrete* ]``

``plane_name`` is assembled from the name of the collection to which belongs the object (if any), the name of the object, and the original id of the face/plane in blender before export (overwritten during the merge into a single object):
``plane_name = collection_name-object_name-original_face_id``
See below for instructions on how to display faces ids in blender view port.


## Geometry check

To comply with how CATT handles geometries, it is suggested to check before export that:
- Faces normals are pointing towards the "inside" of the scene (e.g. inwards for walls, outwards for furnitures)
- Faces are flat (see below). The "triangulate faces" option can be used to ensure this condition

Use the ``Detect non-flat faces`` utility (after selecting an object in 3d view), coupled with blender internal utility (in edit mode) under ``Mesh/Clean Up/Split Non-Planar Faces``, to manually fix non-flat faces. Use ``Mesh/Clean Up/Make Planar Faces`` at your own risk (i.e. not).

### Ensure flat faces

CATT can only handle flat faces/planes. If the model contains non-flat faces, it is recommended to either use the add-on "triangulate faces" option upon export, or to fix the blender meshes using internal tools:
- in edit mode, select all the mesh faces, go to the mesh menu, then clean up and make planar faces (after switching to face select mode).
– and/or look in the properties menu (N key) in edit mode, and use "mesh analysis" > type: distortion, which will let you see the ill-conditioned faces.
- and/or use the 3D Print add-on, set a low angle into "distortion" and press the check button to see the ill-conditioned faces

### Show faces id in blender viewport

from https://blender.stackexchange.com/questions/3249/show-mesh-vertices-id:

- click ``Edit > Preferences``
- in the Display panel of the Interface tab, tick ``Developer Extras``
- (or type ``bpy.context.preferences.view.show_developer_ui = True`` into the Python console)
- open the Overlays popover in the 3D View Overlays popover (top right of the 3D view)
- look for the label Developer and tick the check box ``Indices``


## Flag faces for automatic edge scattering in CATT

Adding a * to the end of an object name will flag its face for automatic edge scattering in CATT upon export. Adding a * to the end of a collection name will flag its direct children (only work on 1st level children) objects faces for automatic edge scattering in CATT upon export.

## Weird face normal inversion during export

If parts of the objects in the scene have their normals that gets inverted during the export (while others don't), it is likely because they have a negative scale. Select the object and use the "apply scale" operator.

Note: worst case scenario, if the first object processed during the export (can be any in the scene) has a negative scale, and all the others have a positive scale, the normal of all but the first object will be reversed during export. Conclusion: keep objects scale positive.

## Using exported model in CATT-Acoustic

Remove default audience plane in CATT, else model import will raise an error because first face in model is not necessarily horizontal (while audience plane should be)


## Export CATT model to Blender

This operation is not a feature of the add-on, simply a list of steps to follow if one needs to import an existing CATT model into Blender.

### Export scene

In CATT, while the focus is on the main window (the one with the "Save and Run" button), click on "File > Export Geometry to > VRML Browser WRL". Select the following parameters:
- disable triangulation
- disable show edges
- to avoid unnecessary overheads, you may as well disable all options

### Fix exported scene coordinates

After import of the WRL file in blender, ensure that your scene coordinate system match CATT's original:
- rotate the whole scene (rooms, listeners, sources) around center along Z axis of 180 degrees
- rotate each individual listener along local center in local coordinate system:
    - rot -90° along X axis ( keys sequence: "r x x -90 enter" )
    - rot 90° along Z axis  ( keys sequence: "r z z 90 enter" )

The reverse operation is not necessary: a scene created in Blender and exported to CATT will have the correct coordinates.

### Fix imported materials

CATT to WRL to Blender export/import will not not preserve material naming. To avoid having to reassign them by hand:
- make sure every material in your CATT scene has a different RGB value (to within +/-1 on at least one component)
- export WRL, import into Blender. Use Blender 2.79b as the WRL import add-on currently does not handle material import in Blender 2.9 or higher
- save the scene, close Blender 2.79b, re-open in Blender 2.93 or higher
- to rename materials, follow the instruction in the script in ./utils/fix_wrl_materials.py and run it from the Blender editor
- to set catt materials properties (optional), follow the instruction in the script in ./utils/define_catt_materials.py and run it from the Blender editor


## Notes on design choice

The merging operation applied on the scene objects upon export (behind the hood, no actual object in the scene will be merged) removes problems previously encountered with handling planes/corners ids overlaps during multi .GEO file export. This step also simplifies the addition of the "remove duplicate vertices" step during the export. This step is necessary to create a .GEO file with no redundant corners while using a blender scene composed of multiple objects.
