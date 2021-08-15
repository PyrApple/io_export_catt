

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
- look for the label Developer and tick the checkbox ``Indices``


## Flag faces for automatic edge scattering in CATT

Adding a * to the end of an object name will flag its face for automatic edge scattering in CATT upon export. Adding a * to the end of a collection name will flag its direct children (only work on 1st level children) objects faces for automatic edge scattering in CATT upon export.


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


## Notes on design choice

The merging operation applied on the scene objects upon export (behind the hood, no actual object in the scene will be merged) removes problems previously encountered with handling planes/corners ids overlaps during multi .GEO file export. This step also simplifies the addition of the "remove duplicate vertices" step during the export. This step is necessary to create a .GEO file with no redundant corners while using a blender scene composed of multiple objects.
