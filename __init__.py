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
    "name": "Catt-Acoustic Export Toolbox",
    "author": "David Poirier-Quinot",
    "blender": (2, 75, 0),
    "location": "3D View > Toolbox",
    "description": "Utility for Catt-Acoustic model export",
    "warning": "",
    "support": 'COMMUNITY',
    "category": "Mesh"}

if "bpy" in locals():
    import importlib
    importlib.reload(ui)
    importlib.reload(operators)
else:
    import bpy
    from bpy.props import (
            StringProperty,
            BoolProperty,
            IntProperty,
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
            )

import math

class CattExportSettings(PropertyGroup):
    export_path = StringProperty(
            name="Export Directory",
            description="Path to directory where the files are created",
            default="//", maxlen=1024, subtype="DIR_PATH",
            )
    master_file_name = StringProperty(
            name="Master File Name",
            description=".GEO file created at export",
            default="MASTER", maxlen=1024,
            )
    display_normals = BoolProperty(
            name="Display Normals",
            description='Display model normals',
            default=False,
            )
    triangulate_faces = BoolProperty(
            name="Triangulate Model",
            description='Transform quads to tri at export',
            default=False,
            )

classes = (
    ui.CattExportToolBarObject,
    ui.CattExportToolBarMesh,
    operators.CattDefaultOperator,
    operators.CattExportRoom,
    operators.CattMaterialCreate,
    operators.CattMaterialConvert,
    CattExportSettings,
    )


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.catt_export = PointerProperty(type=CattExportSettings)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.catt_export
