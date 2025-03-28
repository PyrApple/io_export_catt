# Catt-Acoustic Import/Export Utility

Blender add-on to import and export files from Catt-Acoustic.

## Export Source and Receiver

If the ``Object/Animation`` option is selected, the add-on will export as many objects as there are frames in the Start/End of the playback/rendering range. The ``Merge Distance`` value will determine the minimum distance required between two of these objects, deleting any one object too close from already existing object.

## Import Room

Suggest to use .geo files exported from TUCT, creating a parser-friendly version of the file (replacing catt procedural syntax with explicit definitions).

## Export Room

All the meshes in the room collection need to have only catt materials. Exported plane names are assembled from the name of the object's parent collection, its name and the id of the face/plane.

Check before export that faces normals point towards the "inside" of the room (inwards for walls, outwards for furnitures), and that faces are flat using the ``Detect non-flat faces`` button of the add-on.

### Flag faces for automatic edge diffraction in catt

Adding a * to the end of an object name will flag its face for automatic edge diffraction in catt upon export. Adding a * to the end of a collection name will flag its direct children (only work on 1st level children) objects faces for automatic edge diffraction in catt upon export.

### Merge Objects

If the ``Merge Objects`` option is selected, make sure that all your objects (only need to be the first of the collection really) have all the other objects materials in their material slots.

The merging operation applied on the scene objects upon export removes problems previously encountered with handling planes/corners ids overlaps during multi .geo file export. This step also simplifies the addition of the "remove duplicate vertices" step during the export. This step is necessary to create a .geo file with no redundant corners while using a blender scene composed of multiple objects.


### Ensure that rooms have flat faces

catt does not support non-flat faces/planes. If the model contains non-flat faces, it is recommended to either use the add-on ``triangulate faces`` option upon export, or to fix the blender meshes using internal tools:
- in edit mode, select all the mesh faces, go to the mesh menu, then clean up and make planar faces (after switching to face select mode).
– and/or look in the properties menu (N key) in edit mode, and use ``mesh analysis > type: distortion``, which will let you see the ill-conditioned faces.
- and/or use the 3D Print add-on, set a low angle into ``distortion`` and press the check button to see the ill-conditioned faces

### Identify problematic faces in the blender view port

From https://blender.stackexchange.com/questions/3249/show-mesh-vertices-id:

- click ``Edit > Preferences``
- in the Display panel of the Interface tab, tick ``Developer Extras``
- (or type ``bpy.context.preferences.view.show_developer_ui = True`` into the Python console)
- open the Overlays pop-over in the 3D View Overlays pop-over (top right of the 3D view)
- look for the label Developer and tick the check box ``Indices``

To track down those faces catt reports as non-planar in blender, use these indices and a .geo file exported with the option "Merge Objects" disabled, as enabling this option messes with face ids during export.


### Weird face normal inversion during export

If parts of the objects in the scene have their normals that gets inverted during the export (while others don't), it is likely because they have a negative scale. Select the object and use the "apply scale" operator.

Note: worst case scenario, if the first object processed during the export (can be any in the scene) has a negative scale, and all the others have a positive scale, the normal of all but the first object will be reversed during export. Conclusion: keep objects scale positive.


## Using the exported room in Catt-Acoustic

Uncheck the default audience plane option in catt, else model import will raise an error because first face in model is not necessarily horizontal (while audience plane should be).


## Import Room from CATT-Acoustic

This operation is not a feature of the add-on, simply a list of steps to follow if one needs to import an existing catt model into blender.

### Export Room from catt

In catt, while the focus is on the main window (the one with the ``Save and Run`` button), click on ``File > Export Geometry to > VRML Browser WRL``. Select the following parameters:
- disable triangulation
- disable show edges
- to avoid unnecessary overheads, you may as well disable all options

### Fix exported scene coordinates

After import of the WRL file in blender, ensure that your scene coordinate system match catt's original:
- rotate the whole scene (rooms, listeners, sources) around center along Z axis of 180 degrees
- rotate each individual listener along local center in local coordinate system:
    - rot -90° along X axis ( keys sequence: "r x x -90 enter" )
    - rot 90° along Z axis  ( keys sequence: "r z z 90 enter" )

The reverse operation is not necessary: a scene created in blender and exported to catt will have the correct coordinates.


### Fix imported materials

Catt to WRL to blender export/import will not not preserve material naming. To avoid having to reassign them by hand:
- Make sure every material in your catt scene has a different RGB value (to within +/-1 on at least one component)
- Export WRL, import into blender. Use blender 2.79b as the WRL import add-on currently does not handle material import in blender 2.9 or higher
- Save the scene, close blender 2.79b, re-open in blender 2.93 or higher
- To rename materials, follow the instruction in the script in ./utils/fix_wrl_materials.py and run it from the blender editor
- To set catt materials properties (optional), follow the instruction in the script in ./utils/define_catt_materials.py and run it from the blender editor

