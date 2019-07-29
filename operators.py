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

# All Operator

import bpy
import bmesh
from bpy.types import Operator
from bpy.props import (
        StringProperty,
        BoolProperty,
        IntProperty,
        FloatProperty,
        FloatVectorProperty,
        EnumProperty,
        PointerProperty,
        )


def catt_sanityCheck(context):
    """ returns error if selected objects has usable materials """
    for obj in context.selected_objects:
        if obj.type != 'MESH':
            return 'Object is not a mesh, Aborted'
        for mat in obj.data.materials:
            if mat:
                return False
                return 'Object already has materials, Aborted.'
    return False

def catt_createMaterial(context, name):
    mat = bpy.data.materials.new(name)
    catt_setMaterialProps(mat)
    return mat

def catt_setMaterialProps(mat):
    # Set props
    default_abs = 40.0
    mat['abs_0'] = default_abs
    mat['abs_1'] = default_abs
    mat['abs_2'] = default_abs
    mat['abs_3'] = default_abs
    mat['abs_4'] = default_abs
    mat['abs_5'] = default_abs
    mat['abs_6'] = default_abs
    mat['abs_7'] = default_abs

    default_diff = 50.0
    mat['dif_0'] = default_diff
    mat['dif_1'] = default_diff
    mat['dif_2'] = default_diff
    mat['dif_3'] = default_diff
    mat['dif_4'] = default_diff
    mat['dif_5'] = default_diff
    mat['dif_6'] = default_diff
    mat['dif_7'] = default_diff

    # set identity
    mat['cattMaterial'] = True

    return 1

def catt_checkForCattMaterial(obj):
    error = ''
    warning = ''
    print(len(obj.data.materials))
    print(obj.data.materials)
    if len(obj.data.materials) == 0:
        error = 'Room must have at least one material'
    # when object has no material, somehow obj.data.materials still contains
    # "<bpy_collection[1], IDMaterials>" which is of NoneType
    elif len(obj.data.materials) == 1 and obj.data.materials[0] is None:
        error = 'Room must have at least one material'
    else:
        for mat in obj.data.materials:
            if 'abs_0' not in mat:
                warning = 'Room has at least 1 non Catt material: setting default abs/diff values'
                catt_setMaterialProps(mat)
    return error, warning

def catt_assignMaterial(context, mat):
    ''' assign material to all selected objects, overriding all mat slots'''
    for obj in context.selected_objects:
        # obj.data.materials.clear()
        obj.data.materials.append(mat)


class CattMaterialCreate(Operator):
    """Create an catt material"""
    bl_label = "New Catt Material"
    bl_idname = 'catt.matcreate'
    bl_options = {'REGISTER', 'UNDO'}

    MatName = bpy.props.StringProperty(name='Material Name', default='CattMat')

    def execute(self, context):
        error = catt_sanityCheck(context)
        if not error:
            mat = catt_createMaterial(context, self.MatName)
            catt_assignMaterial(context, mat)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, error)
            return {'CANCELLED'}

# ---------
# ------
# Export

class CattExportRoom(Operator):
    """Export active object as catt room"""
    bl_idname = "catt.export_room"
    bl_label = "Catt Export"

    def execute(self, context):
        # scene = bpy.context.scene
        # catt_export = scene.catt_export
        from . import export

        # Check if export possible
        error = ''
        warning = ''
        ret = 0

        # check for a single object (room) selected
        if len(context.selected_objects) != 1:
            error = 'Select a single object to be exported as room'
        else:
            # check for abs/diff values in obj materials
            obj = context.selected_objects[0]
            error, warning = catt_checkForCattMaterial(obj)

        if warning:
            self.report({'WARNING'}, warning)

        if error:
            self.report({'ERROR'}, error)
            return {'CANCELLED'}
        else:
            info = []
            err = export.catt_export_room(context)
            # report.update(*info)

            if err == 0:
                self.report({'INFO'}, 'Catt export complete')
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, 'Catt export aborted, check in the console for more details')
                return {'CANCELLED'}

class CattMaterialConvert(Operator):
    """Convert material to Catt Material"""
    bl_idname = "catt.convert_to_catt_material"
    bl_label = "Convert to Catt Material"

    def execute(self, context):
        # scene = bpy.context.scene
        # catt_export = scene.catt_export

        obj = context.object
        mat = obj.active_material

        ret = catt_setMaterialProps(mat)


        if ret:
            return {'FINISHED'}
        else:
            return {'CANCELLED'}


# ---------
class CattDefaultOperator(Operator):
    """TODELETE"""
    bl_idname = "catt.not_implemented"
    bl_label = "..."

    def execute(self, context):
        self.report({'WARNING'}, 'Not Implemented')
        return {'CANCELLED'}

