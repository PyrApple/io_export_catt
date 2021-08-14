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

import os
import bpy
import bmesh
from bpy.types import Operator
from bpy.props import StringProperty


# convert material to catt material
class CattMaterialConvert(Operator):

    # init locals
    bl_idname = "catt.convert_to_catt_material"
    bl_label = "Convert to Catt Material"

    def execute(self, context):

        # get active material
        mat = context.object.active_material

        # flag as catt material
        mat['is_catt_material'] = True

        # loop over frequency bands
        nFreqBands = 8
        for iFreq in range(nFreqBands):
            mat['abs_{0}'.format(iFreq)] = 40.0
            mat['dif_{0}'.format(iFreq)] = 50.0

        # disable use nodes (easier to access diffuse color that way)
        mat.use_nodes = False

        return {'FINISHED'}


# convert catt material from previous version of the addon to current
class CattMaterialRetroCompatibility(Operator):

    bl_idname = "catt.convert_catt_material_from_old_to_new"
    bl_label = "Convert to new Catt Material"

    def execute(self, context):

        obj = context.object
        mat = obj.active_material

        mat['is_catt_material'] = mat['cattMaterial']
        del mat['cattMaterial']

        mat.use_nodes = False

        return {'FINISHED'}


# export active object as catt room
class CattExportRoom(Operator):

    # init locals
    bl_idname = "catt.export_room"
    bl_label = "Catt Export"

    def execute(self, context):

        # init local
        catt_export = context.scene.catt_export

        # get list of objects to export (meshes visible in viewport)
        objects = [obj for obj in bpy.context.view_layer.objects if obj.visible_get() and obj.type == 'MESH']

        # check for catt materials
        for obj in objects:

            # no material or dummy material?
            # obj.data.materials sometimes contains single NoneType element when object has no materials
            if len(obj.data.materials) == 0 or (len(obj.data.materials) == 1 and obj.data.materials[0] is None):
                self.report({'ERROR'}, 'object {0} has no materials'.format(obj.name))
                return {'CANCELLED'}

            # not catt materials?
            for mat in obj.data.materials:
                if 'is_catt_material' not in mat:
                    self.report({'ERROR'}, 'object {0} material {1} is not a CATT material'.format(obj.name, mat.name))
                    return {'CANCELLED'}

        # get export path
        export_path = bpy.path.abspath(catt_export.export_path)
        file_name = catt_export.master_file_name + ".GEO"
        file_path = os.path.join(export_path, file_name)

        # export objects
        self.export_objects(file_path, objects)

        # exit
        self.report({'INFO'}, 'CATT export complete')
        return {'FINISHED'}


    # remove * from collection name if need be
    def remove_trailing_asterix(self, name):

        if( len(name) == 0 or name[-1] != '*'):
            return name
        else:
            return name[0:len(name) - 1]


    def export_objects(self, file_path, objects):

        # init locals
        catt_export = bpy.context.scene.catt_export
        bmesh_faces_info = []
        bmeshes = []
        material_names = dict()

        # convert objects to bmeshes, extract valuable face info for later
        for obj in objects:

            # add object material names to global list
            for mat in obj.data.materials:
                if mat.name not in material_names:
                    material_names[mat.name] = mat

            # convert obj to bmesh
            bm = bmesh_copy_from_object(obj, transform=True, triangulate=catt_export.triangulate_faces, apply_modifiers=catt_export.apply_modifiers)
            bmeshes.append(bm)

            # keep track of object collection
            collection_name = '' if len(obj.users_collection) == 0 else obj.users_collection[0].name

            # loop over faces
            for face in bm.faces:

                # keep track of face material
                mat_name = obj.material_slots[face.material_index].material.name

                # save face info to local
                bmesh_faces_info.append({'material_name' : mat_name, 'collection_name' : collection_name, 'object_name' : obj.name})

        # concat into single mesh
        bm_concat = bmesh.new()
        mesh = bpy.data.meshes.new("tmp_mesh")
        for bm in bmeshes:
            bm.to_mesh(mesh)
            bm_concat.from_mesh(mesh)
            bm.free()

        # remove duplicates
        bmesh.ops.remove_doubles(bm_concat, verts=bm_concat.verts, dist=0.001)

        # required lookup table rebuild
        # warning: may temper with the ordering of bmesh faces and its matching with built list bmesh_faces_info
        bm_concat.faces.ensure_lookup_table()

        # open file
        with open(file_path, 'w', newline='\r\n') as data:

            # init write
            fw = data.write

            # header
            fw(';file generated by the blender catt export add-on from: \n;{0} \n\n'.format(bpy.data.filepath))

            # materials
            fw(';MATERIALS\n\n')
            r = 1 # round factor
            for mat in material_names.values():
                fw("abs {0} = <{1} {2} {3} {4} {5} {6} : {7} {8} > L < {9} {10} {11} {12} {13} {14} : {15} {16}> {{{17} {18} {19}}} \n".format(mat.name, round(mat['abs_0'], r), round(mat['abs_1'], r), round(mat['abs_2'], r), round(mat['abs_3'], r), round(mat['abs_4'], r), round(mat['abs_5'], r), round(mat['abs_6'], r), round(mat['abs_7'], r), round(mat['dif_0'], r), round(mat['dif_1'], r), round(mat['dif_2'], r), round(mat['dif_3'], r), round(mat['dif_4'], r), round(mat['dif_5'], r), round(mat['dif_6'], r), round(mat['dif_7'], r), int(100*mat.diffuse_color[0]), int(100*mat.diffuse_color[1]), int(100*mat.diffuse_color[2])))

            # vertices
            fw('\nCORNERS\n\n')
            for vertice in bm_concat.verts:
                fw("{0} {1:.2f} {2:.2f} {3:.2f} \n".format(vertice.index + 1, vertice.co[0], vertice.co[1], vertice.co[2]) )

            # faces
            fw('\nPLANES\n\n')
            for iFace in range(len(bm_concat.faces)):

                # init locals
                face = bm_concat.faces[iFace]
                collection_name = bmesh_faces_info[iFace]['collection_name']
                object_name = bmesh_faces_info[iFace]['object_name']
                material_name = bmesh_faces_info[iFace]['material_name']

                # auto edge scattering if collection or object names end with '*'
                edgeScatteringStr = ''
                if( len(collection_name) > 0 and collection_name[-1] == '*' ):
                    edgeScatteringStr = '*'
                    collection_name = self.remove_trailing_asterix(collection_name)
                if( object_name[-1] == '*' ):
                    object_name = self.remove_trailing_asterix(object_name)
                    edgeScatteringStr = '*'

                # shape face name from collection and object names
                # 'Master Collection' is the name of blender root collection
                if collection_name == '' or collection_name == 'Master Collection':
                    faceName = object_name
                else:
                    faceName = collection_name + '-' + object_name

                # get face vertice ids
                vertList = [vertice.index + 1 for vertice in face.verts]
                vertListStr = ' '.join(map(str, vertList))

                # write face line
                fw("[ {0} {1} / {2} / {3}{4} ]\n".format(face.index + 1, faceName, vertListStr, material_name, edgeScatteringStr) )

        # free bmesh
        bm_concat.free()

        # return
        print('catt add-on: file saved at {0}'.format(file_path))
        return 0


# method from the Print3D add-on: create a bmesh from an object
# (for triangulation, apply modifiers, etc.)
def bmesh_copy_from_object(obj, transform=True, triangulate=True, apply_modifiers=False):
    """Returns a transformed, triangulated copy of the mesh"""

    assert obj.type == 'MESH'

    if apply_modifiers and obj.modifiers:
        import bpy
        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)
        me = obj_eval.to_mesh()
        bm = bmesh.new()
        bm.from_mesh(me)
        obj_eval.to_mesh_clear()
    else:
        me = obj.data
        if obj.mode == 'EDIT':
            bm_orig = bmesh.from_edit_mesh(me)
            bm = bm_orig.copy()
        else:
            bm = bmesh.new()
            bm.from_mesh(me)

    # TODO. remove all customdata layers.
    # would save ram

    if transform:
        bm.transform(obj.matrix_world)

    if triangulate:
        bmesh.ops.triangulate(bm, faces=bm.faces)

    return bm
