# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "CATT-Acoustic",
    "author": "David Poirier-Quinot",
    "blender": (4, 0, 0),
    "location": "3D View > Sidebar",
    "description": "Transfer data between CATT-Acoustic and Blender",
    "doc_url": "https://github.com/PyrApple/io_export_catt/tree/master",
    "support": 'COMMUNITY',
    "category": "Import-Export"}

if "bpy" in locals():

    import importlib
    importlib.reload(ui)
    importlib.reload(operators)
    importlib.reload(utils)

else:

    import bpy

    from bpy.props import (
        StringProperty,
        BoolProperty,
        # IntProperty,
        FloatProperty,
        FloatVectorProperty,
        EnumProperty,
        PointerProperty,
    )

    from bpy.types import (
        Operator,
        AddonPreferences,
        PropertyGroup,
    )

    from . import (
        ui,
        operators,
        utils,
    )


def get_embedded_text_names(self, context):
    """populate comments drop down with embedded text file names"""

    # init
    out = []
    out.append(("DISABLED", "Disabled", "", 1))

    # loop over text files
    for i_key, key in enumerate(bpy.data.texts.keys()):
        out.append((key, key, "", i_key+2))

    return out


class SceneProperties(PropertyGroup):

    export_path: StringProperty(
        name="Export Folder",
        description="Path to the directory where the file will be saved",
        default="//",
        maxlen=1024,
        subtype="DIR_PATH",
    )

    debug: BoolProperty(
        name="Show Console Logs",
        description='Print logs to blender console',
        default=False,
    )

    room_file_name: StringProperty(
        name="File",
        description="Name of the room file created upon export",
        default="master.geo",
        maxlen=1024,
    )

    triangulate_faces: BoolProperty(
        name="Triangulate Faces",
        description='Transform ngons in triangles upon export',
        default=False,
    )

    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        description='Apply objects modifiers upon export',
        default=False,
    )

    merge_objects: BoolProperty(
        name="Merge Objects",
        description='Merge objects into single mesh upon export (enables remove duplicate vertices)',
        default=False,
    )

    frequency_bands: FloatVectorProperty(
        name="Frequency Bands",
        description='Frequency bands (in Hz) for which absorption/diffraction coefs are defined',
        size=8,
        default=(125, 250, 500, 1000, 2000, 4000, 8000, 16000),
    )

    rm_duplicates_dist: FloatProperty(
        name="Merge Vertices Distance",
        description='Distance (in m) below which two vertices are merged when creating the export mesh',
        default=1e-7,
        min=0.0, max=1.0, soft_min=0.0, soft_max=1.0,
    )

    export_face_ids: BoolProperty(
        name="Export Face IDs",
        description='Add face id information in exported plane names (for debug purpose)',
        default=False,
    )

    # export_progress: IntProperty(
    #         name="Progress", description="",
    #         default=0,
    #         min=0, max=100,
    #         step=1, subtype='PERCENTAGE'
    #         )

    editor_scripts: EnumProperty(
        name="Comments",
        description="Select an embedded text, its content will be added as comments at the top of the exported .GEO file",
        items=get_embedded_text_names,
    )

    room_collection: StringProperty(
        name="Room",
        description="Collection of objects to export as room",
        default="", maxlen=1024,
    )

    receiver_file_name: StringProperty(
        name="File",
        description="Name of the file created upon export",
        default="rec.loc",
        maxlen=1024,
    )

    receiver_object: StringProperty(
        name="Receiver",
        description="Object which animation will be exported as receiver positions",
        default="", maxlen=1024,
    )

    receiver_collection: StringProperty(
        name="Receivers",
        description="Collection of objects to export as receivers",
        default="", maxlen=1024,
    )

    receiver_export_type: EnumProperty(
        name="Export",
        description="Export either animated object or collection of objects",
        items=[("ANIMATED", "Object/Animation", ""), ("COLLECTION", "Collection", "")],
        default="COLLECTION"
    )

    receiver_dist_thresh: FloatProperty(
        name="Merge Distance",
        description="Minimum distance (in m) between two exported positions along animation curve",
        default=0,
        min=0.0, max=100.0, soft_min=0.0, soft_max=100.0,
    )

    source_file_name: StringProperty(
        name="File",
        description="Name of the file created upon export",
        default="src.loc",
        maxlen=1024,
    )

    source_object: StringProperty(
        name="Source",
        description="Object which animation will be exported as source positions",
        default="", maxlen=1024,
    )

    source_collection: StringProperty(
        name="Sources",
        description="Collection of objects to export as sources",
        default="", maxlen=1024,
    )

    source_export_type: EnumProperty(
        name="Export",
        description="Export either animated object or collection of objects",
        items=[("ANIMATED", "Object/Animation", ""), ("COLLECTION", "Collection", "")],
        default="COLLECTION"
    )

    source_dist_thresh: FloatProperty(
        name="Merge Distance",
        description="Minimum distance (in m) between two exported positions along animation curve",
        default=0,
        min=0.0, max=100.0, soft_min=0.0, soft_max=100.0,
    )


classes = (
    SceneProperties,
    ui.VIEW3D_PT_catt_main,
    ui.VIEW3D_PT_catt_material,
    operators.MESH_OT_catt_import,
    operators.MESH_OT_catt_export_room,
    operators.MESH_OT_catt_export_receiver_animation,
    operators.MESH_OT_catt_export_receiver_collection,
    operators.MESH_OT_catt_export_source_animation,
    operators.MESH_OT_catt_export_source_collection,
    operators.MESH_OT_catt_material_convert,
    # operators.MESH_OT_catt_material_retro_compat,
    operators.MESH_OT_catt_utils,
)


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.catt_io = PointerProperty(type=SceneProperties)

def unregister():

    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.catt_io
