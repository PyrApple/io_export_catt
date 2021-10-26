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
    "name": "CATT-Acoustic export utility",
    "author": "David Poirier-Quinot",
    "blender": (2, 93, 0),
    "location": "3D View > Sidebar",
    "description": "Utility for exporting Blender scenes to CATT-Acoustic GEO files",
    "doc_url": "https://github.com/PyrApple/io_export_catt/blob/master/readme.md",
    "support": 'COMMUNITY',
    "category": "Mesh"}

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
            # EnumProperty,
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


class SceneProperties(PropertyGroup):

    export_path: StringProperty(
            name="Export Directory",
            description="Path to the directory where the file will be saved",
            default="//",
            maxlen=1024,
            subtype="DIR_PATH",
            )
    master_file_name: StringProperty(
            name="Export File Name",
            description="Name of the file created upon export",
            default="MASTER.GEO",
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
    debug: BoolProperty(
            name="Write Logs To Console",
            description='Print progress log to blender console during export',
            default=False,
            )
    # export_progress: IntProperty(
    #         name="Progress", description="",
    #         default=0,
    #         min=0, max=100,
    #         step=1, subtype='PERCENTAGE'
    #         )


classes = (
    SceneProperties,

    ui.VIEW3D_PT_catt_instruction,
    ui.VIEW3D_PT_catt_export,
    ui.VIEW3D_PT_catt_material,

    operators.MESH_OT_catt_export,
    operators.MESH_OT_catt_material_convert,
    # operators.MESH_OT_catt_material_retro_compat,
    operators.MESH_OT_catt_utils,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.catt_export = PointerProperty(type=SceneProperties)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.catt_export
