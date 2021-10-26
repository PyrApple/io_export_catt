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

def get_material_template(context):

    # init locals
    mat = {}
    catt_export = context.scene.catt_export

    # is material converted to catt material (has all the required properties)
    mat["is_catt_material"] = {
        "description": 'Flag material as a CATT material',
        "default":1, "soft_min":0, "soft_max":1,
        "min": 0, "max": 1
    }

    # should material use diffraction coefficients upon export?
    mat["use_diffraction"] = {
        "description": 'Use diffraction coefficients',
        "default":1, "soft_min":0, "soft_max":1,
        "min": 0, "max": 1
    }

    # should material be exported with diff estimate option?
    mat['is_diff_estimate'] = {
        "description": 'Use diffraction estimate',
        "default":0, "soft_min":0, "soft_max":1,
        "min": 0, "max": 1
    }

    # if so, what is its diff estimate value?
    mat['diff_estimate'] = {
        "description": 'Diffraction estimate value',
        "default":0.1, "soft_min":0.0, "min": 0.0
    }


    # loop over frequency bands
    for i_freq, freq in enumerate(catt_export.frequency_bands):

        # prepare rna ui (for soft lock, description, etc.)
        mat['abs_{0}'.format(i_freq)] = {
            "description": 'Absorption coef at {0}'.format(utils.freq_to_str(freq)),
            "default":40.0, "soft_min":0.0, "soft_max":100.0,
            "min": 0.0, "max": 100.0
        }
        mat['dif_{0}'.format(i_freq)] = {
            "description": 'Diffraction coef at {0}'.format(utils.freq_to_str(freq)),
            "default":50.0, "soft_min":0.0, "soft_max":100.0,
            "min": 0.0, "max": 100.0
        }

    return mat


class MESH_OT_catt_material_convert(Operator):
    """ operator used to convert material to catt material """

    # init locals
    bl_idname = "catt.convert_to_catt_material"
    bl_label = "Convert to Catt Material"


    def execute(self, context):
        """ method called from ui """

        # init locals
        catt_export = context.scene.catt_export

        # get active material
        mat = context.object.active_material

        # get material template
        mat_template = get_material_template(context)
        rna_dict = {}

        for key, value in mat_template.items():

            # retro compatibility
            if key not in mat:
                mat[key] = value["default"]

            rna_dict[key] = value

        # apply rna
        mat["_RNA_UI"] = rna_dict

        # disable use nodes (easier to access diffuse color that way)
        mat.use_nodes = False

        return {'FINISHED'}


# class MESH_OT_catt_material_retro_compat(Operator):
#     """ operator used to convert material to catt material """

#     # init locals
#     bl_idname = "catt.convert_catt_material_from_old_to_new"
#     bl_label = "Convert to new Catt Material"

#     def execute(self, context):
#         """ method called from ui """

#         # init locals
#         catt_export = context.scene.catt_export

#         # get active material
#         mat = context.object.active_material
#         rna_dict = mat["_RNA_UI"]

#         # get template material
#         mat_template = get_material_template(context)

#         # loop over required fields
#         for key, value in mat_template.items():

#             # add if missing
#             if key not in mat:
#                 mat[key] = value["default"]
#                 rna_dict[key] = value

#             else:
#                 # fix if corrupted (without updating value itself, assumes type doesn't change)
#                 if rna_dict[key] != value:
#                     rna_dict[key] = value

#         # apply rna
#         mat["_RNA_UI"] = rna_dict

#         # exit
#         return {'FINISHED'}


class MESH_OT_catt_export(Operator):
    """Export objects of every collection included in the View Layer"""

    # init locals
    bl_idname = "catt.export"
    bl_label = "Catt Export"

    def execute(self, context):
        """ method called from ui """

        # init local
        catt_export = context.scene.catt_export

        # update deprecated materials if need be
        self.update_deprecated_catt_materials(context)

        # get list of objects to export (meshes visible in viewport)
        objects = [obj for obj in bpy.context.view_layer.objects if obj.visible_get() and obj.type == 'MESH']

        # discard if no objects
        if len(objects) == 0:
            self.report({'INFO'}, 'No visible objects to export')
            return {'CANCELLED'}

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


    def update_deprecated_catt_materials(self, context):
        """Update properties of all catt materials to latest version"""

        # init locals
        catt_export = context.scene.catt_export
        mat_template = get_material_template(context)

        # print("----------------------------------------")
        # loop over materials in scene
        for mat in bpy.data.materials:

            # discard if not a catt material
            if "is_catt_material" not in mat:
                continue

            # copy rna
            rna_dict = mat["_RNA_UI"]

            # for key in rna_dict:
            #     print("-", key, rna_dict[key])

            # loop over required fields
            for key, value in mat_template.items():

                # add if missing
                if key not in mat:
                    print("++ key not found, adding key", key, "to", mat.name)
                    mat[key] = value["default"]
                    rna_dict[key] = value

                # # fix if corrupted (without updating value itself, assumes type doesn't change)
                # elif rna_dict[key] != value:
                #     print("deprecated key found, updating key", key, "of", mat.name)
                #     print("\t", rna_dict[key], "->", value)

                #     rna_dict[key] = value

            # apply rna
            mat["_RNA_UI"] = rna_dict

        # exit
        return {'FINISHED'}


    def export_objects(self, file_path, objects):
        """ export list of objects to catt geo file """

        # init locals
        catt_export = bpy.context.scene.catt_export
        objects_copy = []

        for i_obj, obj in enumerate(objects):

            # debug log
            if catt_export.debug:
                print('copying objects {0}/{1}: {2}'.format(i_obj+1, len(objects), obj.name))

            # duplicate object
            obj_copy = obj.copy()
            obj_copy.data = obj_copy.data.copy() # make sure object data is not linked to original

            # apply transform, triangulate, apply modifiers
            bm = utils.bmesh_copy_from_object(obj, transform=False, triangulate=catt_export.triangulate_faces, apply_modifiers=catt_export.apply_modifiers)

            # copy back bmesh to mesh data
            bm.to_mesh(obj_copy.data)
            obj_copy.data.update()
            bm.free()

            # save to locals
            objects_copy.append(obj_copy)

        # is there a join operation to apply?
        if catt_export.merge_objects and len(objects_copy) > 1:

            # debug log
            if catt_export.debug:
                print('merging objects')

            # create tmp context, to avoid changing current user selected object(s)
            ctx = bpy.context.copy()

            # set as active one of the objects to join
            ctx['active_object'] = objects_copy[0]

            # select all objects to join
            ctx['selected_editable_objects'] = objects_copy

            # join objects into one
            bpy.ops.object.join(ctx)

            # get reference to created object
            concat_object = ctx['active_object']

            # remove duplicate vertices
            if catt_export.rm_duplicates_dist > 0:

                # debug
                if catt_export.debug:
                    print('merging neighbor vertices')

                bm = bmesh.new()
                bm.from_mesh(concat_object.data)
                bmesh.ops.remove_doubles(bm, verts = bm.verts, dist = catt_export.rm_duplicates_dist)
                bm.to_mesh(concat_object.data)
                concat_object.data.update()
                bm.free()

            # create new list with only that object
            objects_copy = [concat_object]


        # build list of materials used in objects (unique)
        materials_to_export = []
        for obj in objects_copy:
            [materials_to_export.append(mat) for mat in obj.data.materials]
        materials_to_export = list(set(materials_to_export)) # remove duplicates

        # open file
        with open(file_path, 'w', newline='\r\n') as data:

            # init write
            fw = data.write

            # header
            fw(';file generated by the blender catt export add-on from: \n;{0} \n\n'.format(bpy.data.filepath))

            # materials
            fw(';MATERIALS\n\n')
            r = 1 # round factor

            for i_mat, mat in enumerate(materials_to_export):

                # debug log
                if catt_export.debug:
                    print('exporting materials {0}/{1}: {2} '.format(i_mat+1, len(materials_to_export), mat.name))

                # absorption
                fw("abs {0} = <{1} {2} {3} {4} {5} {6} : {7} {8}>".format(utils.mat_name_to_str(mat.name), round(mat['abs_0'], r), round(mat['abs_1'], r), round(mat['abs_2'], r), round(mat['abs_3'], r), round(mat['abs_4'], r), round(mat['abs_5'], r), round(mat['abs_6'], r), round(mat['abs_7'], r)))

                # diffraction
                if mat["use_diffraction"]:

                    fw(" L ")
                    if mat['is_diff_estimate']:
                        fw("<estimate({0})>".format(round(mat['diff_estimate'], 3)))
                    else:
                        fw("<{0} {1} {2} {3} {4} {5} : {6} {7}>".format(round(mat['dif_0'], r), round(mat['dif_1'], r), round(mat['dif_2'], r), round(mat['dif_3'], r), round(mat['dif_4'], r), round(mat['dif_5'], r), round(mat['dif_6'], r), round(mat['dif_7'], r)))

                fw(" {{{0} {1} {2}}} \n".format(int(255*mat.diffuse_color[0]), int(255*mat.diffuse_color[1]), int(255*mat.diffuse_color[2])))

            # vertices header
            fw('\nCORNERS\n\n')

            vertex_index_offsets = [0] # first one has no offset
            faces_index_offsets = [0] # first one has no offset

            for obj in objects_copy[:-1]:
                vertex_index_offsets.append( len(obj.data.vertices) + vertex_index_offsets[-1])
                faces_index_offsets.append( len(obj.data.polygons) + faces_index_offsets[-1] )

            for i_obj, obj in enumerate(objects_copy):

                # debug log
                if catt_export.debug:
                    print('exporting vertices {0}/{1}: {2} '.format(i_obj+1, len(objects_copy), obj.name))

                for vertice in obj.data.vertices:

                    coords = (obj.matrix_world @ vertice.co)
                    # coords = vertice.co

                    index = vertice.index + vertex_index_offsets[i_obj] + 1
                    fw("{0} {1:.2f} {2:.2f} {3:.2f} \n".format(index, coords[0], coords[1], coords[2]) )


            # faces header
            fw('\nPLANES\n\n')

            for i_obj, obj in enumerate(objects_copy):

                # debug log
                if catt_export.debug:
                    print('exporting faces {0}/{1}: {2} '.format(i_obj+1, len(objects_copy), obj.name))

                for i_face, face in enumerate(obj.data.polygons):

                    # init locals
                    collection_name = '' if len(obj.users_collection) == 0 else obj.users_collection[0].name
                    object_name = obj.name
                    material_name = utils.mat_name_to_str(obj.material_slots[face.material_index].material.name)

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
                    face_name = "{0}-{1}".format(object_name, face.index) # keep original face id (no offset here)
                    if collection_name not in ('', 'Master Collection'):
                        face_name = "{0}-{1}".format(collection_name, face_name)

                    # get face vertice ids
                    offset = vertex_index_offsets[i_obj] + 1
                    vertices_list = [vertice + offset for vertice in face.vertices]
                    vertices_list_str = ' '.join(map(str, vertices_list))

                    # write face line
                    offset = faces_index_offsets[i_obj] + 1
                    fw("[ {0} {1} / {2} / {3}{4} ]\n".format(face.index + offset, face_name, vertices_list_str, material_name, edge_scattering_str) )


        # clean
        for i_obj, obj in enumerate(objects_copy):
            if catt_export.debug:
                print('deleting copied objects {0}/{1}: {2} '.format(i_obj+1, len(objects_copy), obj.name))
            bpy.data.objects.remove(obj)

        # # debug
        # print('remaining objects:')
        # for o in bpy.data.objects:
        #     print("- object:", o.name)

        # return
        print('CATT add-on: file saved at {0}'.format(file_path))
        return 0




from mathutils.geometry import (distance_point_to_plane, normal)


class MESH_OT_catt_utils(Operator):
    """Highlight non-planar faces of the active object (check is more strict than CATT's)"""

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
