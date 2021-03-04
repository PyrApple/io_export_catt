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

# Export wrappers and integration with external tools.

import bpy
import os
from mathutils import Vector
import bmesh

# method from the Print3D add-on: create a bmesh from an object 
# (for triangulation, apply modifiers, etc.)
def bmesh_copy_from_object(obj, transform=True, triangulate=True, apply_modifiers=False):

    assert(obj.type == 'MESH')

    if apply_modifiers and obj.modifiers:
        import bpy
        me = obj.to_mesh(bpy.context.scene, True, 'PREVIEW', calc_tessface=False)
        bm = bmesh.new()
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        del bpy
    else:
        me = obj.data
        if obj.mode == 'EDIT':
            bm_orig = bmesh.from_edit_mesh(me)
            bm = bm_orig.copy()
        else:
            bm = bmesh.new()
            bm.from_mesh(me)

    if transform:
        bm.transform(obj.matrix_world)

    if triangulate:
        bmesh.ops.triangulate(bm, faces=bm.faces)

    return bm


def catt_export_room(context):
    """ Main export method """

    # get locals
    scene = context.scene
    obj = context.active_object
    catt_export = scene.catt_export

    # get bmesh
    bm = bmesh_copy_from_object(obj, transform=True, triangulate=catt_export.triangulate_faces, apply_modifiers=catt_export.apply_modifiers)

    # get export path
    export_path = bpy.path.abspath(catt_export.export_path)
    fileName = catt_export.master_file_name + ".GEO"
    filePath = os.path.join(export_path, fileName)

    # open file
    with open(filePath, 'w') as data:
        fw = data.write

        # Catt related header
        header = ";" + fileName
        fw('%s\r\n' % header)
        header = ";PROJECT="
        fw('%s\r\n\r\n' % header)

        # Blender Add-on related header
        header = ";FILE GENERATED VIA BLENDER CATT EXPORT ADD-ON"
        fw('%s\r\n' % header)
        blendFilename = os.path.splitext(os.path.split(bpy.data.filepath)[1])[0]
        if not blendFilename:
            blendFilename = 'floating file (unsaved)'
        else:
            blendFilename = blendFilename + ".blend"
        header = ";BASED ON .BLEND FILE: " + blendFilename
        fw('%s\r\n\r\n' % header)

        # write material(s)
        header = ""
        for mat in obj.data.materials:
            tmp = "abs {0} = <{1} {2} {3} {4} {5} {6} : {7} {8} > L < {9} {10} {11} {12} {13} {14} : {15} {16}> {{{17} {18} {19}}} \r\n".format(mat.name,int(mat['abs_0']),int(mat['abs_1']),int(mat['abs_2']),int(mat['abs_3']),int(mat['abs_4']),int(mat['abs_5']),int(mat['abs_6']),int(mat['abs_7']),int(mat['dif_0']),int(mat['dif_1']),int(mat['dif_2']),int(mat['dif_3']),int(mat['dif_4']),int(mat['dif_5']),int(mat['dif_6']),int(mat['dif_7']),int(100*mat.diffuse_color[0]),int(100*mat.diffuse_color[1]),int(100*mat.diffuse_color[2]))
            header = header + tmp
        fw('%s\r\n' % header)

        # write corners (vertices)
        header = "CORNERS"
        fw('%s\r\n\r\n' % header)
        for vertice in bm.verts:
            verticeId = vertice.index + 1 # as catt expects ids starting from 1
            fw("{0} {1:.2f} {2:.2f} {3:.2f} \r\n".format(verticeId, vertice.co[0], vertice.co[1], vertice.co[2]) )

        # write planes (faces)
        header = "PLANES"
        fw('\r\n%s\r\n\r\n' % header)
        for face in bm.faces:

            # get face material
            matName = obj.material_slots[face.material_index].material.name
            
            # get face vertice ids
            vertList = [vertice.index + 1 for vertice in face.verts]
            vertListStr = ' '.join(map(str, vertList))
            
            # write face line
            planeName = 'wall' # default plane name set in Catt
            fw("[ {0} {1} / {2} / {3} ]\r\n".format(face.index + 1, 'wall', vertListStr, matName) )

    print('Catt file exported at {0}'.format(filePath))
    return 0
