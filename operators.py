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
from . import utils

class MESH_OT_catt_material_convert(Operator):
    """ operator used to convert material to catt material """

    # init locals
    bl_idname = "catt.convert_to_catt_material"
    bl_label = "Convert to Catt Material"

    def execute(self, context):
        """ method called from ui """

        # init locals
        catt_export = context.scene.catt_export
        rna_dict = {}

        # get active material
        mat = context.object.active_material

        # loop over frequency bands
        for i_freq, freq in enumerate(catt_export.frequency_bands):

            # init property
            mat['abs_{0}'.format(i_freq)] = 40.0
            mat['dif_{0}'.format(i_freq)] = 50.0

            # prepare rna ui (for soft lock, description, etc.)
            rna_dict['abs_{0}'.format(i_freq)] = {
                "description": 'absorption coef at {0}'.format(utils.freq_to_str(freq)),
                "default":40.0, "soft_min":0.0, "soft_max":100.0,
                "min": 0.0, "max": 100.0
            }
            rna_dict['dif_{0}'.format(i_freq)] = {
                "description": 'diffraction coef at {0}'.format(utils.freq_to_str(freq)),
                "default":50.0, "soft_min":0.0, "soft_max":100.0,
                "min": 0.0, "max": 100.0
            }

        # add diff estimate flag and value
        mat['is_diff_estimate'] = False
        rna_dict['is_diff_estimate'] = {
                "description": 'use diffraction estimate',
                "default":0, "soft_min":0, "soft_max":1,
                "min": 0, "max": 1
            }
        mat['diff_estimate'] = 0.1
        rna_dict['diff_estimate'] = {
                "description": 'diffraction estimate value',
                "default":0.1, "soft_min":0.0, "min": 0.0
            }

        # flag as catt material
        mat['is_catt_material'] = True
        rna_dict['is_diff_estimate'] = {
                "description": 'flag material as a CATT material',
                "default":0, "soft_min":0, "soft_max":1,
                "min": 0, "max": 1
            }

        # apply rna
        mat["_RNA_UI"] = rna_dict

        # disable use nodes (easier to access diffuse color that way)
        mat.use_nodes = False

        return {'FINISHED'}


class MESH_OT_catt_export(Operator):
    """Export objects of every collection included in the View Layer"""

    # init locals
    bl_idname = "catt.export"
    bl_label = "Catt Export"

    def execute(self, context):
        """ method called from ui """

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

            # loop over materials
            for mat in obj.data.materials:

                # discard empty material slots (@todo: handle empty material slots during export)
                if mat is None:
                    self.report({'ERROR'}, 'object {0} has empty matrial slot(s), please remove them'.format(obj.name))
                    return {'CANCELLED'}

                # not catt materials?
                if 'is_catt_material' not in mat:
                    self.report({'ERROR'}, 'object {0} material {1} is not a CATT material'.format(obj.name, mat.name))
                    return {'CANCELLED'}

                # material with too long name
                if len(mat.name) > 15:
                    self.report({'ERROR'}, 'object {0} material {1} name is too long (max is 15 characters)'.format(obj.name, mat.name))
                    return {'CANCELLED'}


        # get export path
        export_path = bpy.path.abspath(catt_export.export_path)
        file_name = catt_export.master_file_name
        file_path = os.path.join(export_path, file_name)

        # export objects
        self.export_objects(file_path, objects)

        # exit
        self.report({'INFO'}, 'CATT export complete')
        return {'FINISHED'}


    def export_objects(self, file_path, objects):
        """ export list of objects to catt geo file """

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
            bm = utils.bmesh_copy_from_object(obj, transform=True, triangulate=catt_export.triangulate_faces, apply_modifiers=catt_export.apply_modifiers)
            bmeshes.append(bm)

            # keep track of object collection
            collection_name = '' if len(obj.users_collection) == 0 else obj.users_collection[0].name

            # loop over faces
            for face in bm.faces:

                # keep track of face material
                mat_name = obj.material_slots[face.material_index].material.name

                # save face info to local
                bmesh_faces_info.append({
                    'material_name' : mat_name,
                    'collection_name' : collection_name,
                    'object_name' : obj.name,
                    'face_index': face.index
                    })

        # concat into single mesh
        bm_concat = bmesh.new()
        mesh = bpy.data.meshes.new("tmp_mesh")
        for bm in bmeshes:
            bm.to_mesh(mesh)
            bm_concat.from_mesh(mesh)
            bm.free()

        # remove duplicates
        bmesh.ops.remove_doubles(bm_concat, verts = bm_concat.verts, dist = catt_export.rm_duplicates_dist)

        # required lookup table rebuild
        # warning: may temper with the ordering of bmesh faces and its matching with built list bmesh_faces_info
        # did not stumble onto this problem in tested scenarios yet
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

                # absorption
                fw("abs {0} = <{1} {2} {3} {4} {5} {6} : {7} {8}>".format(mat.name, round(mat['abs_0'], r), round(mat['abs_1'], r), round(mat['abs_2'], r), round(mat['abs_3'], r), round(mat['abs_4'], r), round(mat['abs_5'], r), round(mat['abs_6'], r), round(mat['abs_7'], r)))

                # diffraction
                fw(" L ")
                if mat['is_diff_estimate']:
                    fw("<estimate({0})>".format(round(mat['diff_estimate'], 3)))
                else:
                    fw("<{0} {1} {2} {3} {4} {5} : {6} {7}>".format(round(mat['dif_0'], r), round(mat['dif_1'], r), round(mat['dif_2'], r), round(mat['dif_3'], r), round(mat['dif_4'], r), round(mat['dif_5'], r), round(mat['dif_6'], r), round(mat['dif_7'], r)))

                fw(" {{{0} {1} {2}}} \n".format(int(100*mat.diffuse_color[0]), int(100*mat.diffuse_color[1]), int(100*mat.diffuse_color[2])))

            # vertices
            fw('\nCORNERS\n\n')
            for vertice in bm_concat.verts:
                fw("{0} {1:.2f} {2:.2f} {3:.2f} \n".format(vertice.index + 1, vertice.co[0], vertice.co[1], vertice.co[2]) )

            # faces
            fw('\nPLANES\n\n')
            for i_face, face in enumerate(bm_concat.faces):

                # init locals
                collection_name = bmesh_faces_info[i_face]['collection_name']
                object_name = bmesh_faces_info[i_face]['object_name']
                material_name = bmesh_faces_info[i_face]['material_name']
                face_index = bmesh_faces_info[i_face]['face_index']

                # auto edge scattering if collection or object names end with '*'
                edge_scattering_str = ''
                if( len(collection_name) > 0 and collection_name[-1] == '*' ):
                    edge_scattering_str = '*'
                    collection_name = collection_name.rstrip('*')
                if object_name[-1] == '*':
                    object_name = object_name.rstrip('*')
                    edge_scattering_str = '*'

                # shape face name from collection and object names
                # 'Master Collection' is the name of blender root collection
                face_name = "{0}-{1}".format(object_name, face_index)
                if collection_name not in ('', 'Master Collection'):
                    face_name = "{0}-{1}".format(collection_name, face_name)

                # get face vertice ids
                vertices_list = [vertice.index + 1 for vertice in face.verts]
                vertices_list_str = ' '.join(map(str, vertices_list))

                # write face line
                fw("[ {0} {1} / {2} / {3}{4} ]\n".format(face.index + 1, face_name, vertices_list_str, material_name, edge_scattering_str) )

        # free bmesh
        bm_concat.free()

        # return
        print('CATT add-on: file saved at {0}'.format(file_path))
        return 0


from mathutils.geometry import (distance_point_to_plane, normal)


class MESH_OT_catt_utils(Operator):
    """Highlight non-planar faces of the active object"""

    # init locals
    bl_idname = "catt.utils"
    bl_label = "Catt Utils"

    # shape input argument
    arg: bpy.props.StringProperty(name='arg', default='')

    def execute(self, context):
        """ method called from ui """

        # init local
        catt_export = context.scene.catt_export

        # check for non flat faces
        if self.arg == 'check_nonflat_faces':

            # discard if no object selected
            sel_objects = bpy.context.selected_objects
            if( len(sel_objects) == 0 ):
                self.report({'INFO'}, 'No object selected.')
                return {'CANCELLED'}

            # switch to edit mode
            bpy.ops.object.mode_set(mode = 'EDIT')

            # context = bpy.context
            # obj = context.edit_object
            mesh = bpy.context.edit_object.data

            # select None
            bpy.ops.mesh.select_all(action='DESELECT')
            bm = bmesh.from_edit_mesh(mesh)
            ngons = [f for f in bm.faces if len(f.verts) > 3]

            # init locals
            has_non_flat_faces = False
            planar_tolerance = 1e-6

            # loop over faces
            for ngon in ngons:

                # define a plane from first 3 points
                co = ngon.verts[0].co
                norm = normal([v.co for v in ngon.verts[:3]])

                # set face selected
                ngon.select = not all( [abs(distance_point_to_plane(v.co, co, norm)) < planar_tolerance for v in ngon.verts[3:]] )

                # flag at least one non flat face detected
                if ngon.select:
                    has_non_flat_faces = True

            # update mesh
            bmesh.update_edit_mesh(mesh)

            # disable edit mode if no non-flat face detected
            if not has_non_flat_faces:
                bpy.ops.object.mode_set(mode = 'OBJECT')
                self.report({'INFO'}, 'No non-flat face detected.')

            return {'FINISHED'}




