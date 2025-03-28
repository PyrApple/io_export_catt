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
import mathutils
import math
import bmesh
from bpy.types import Operator
from . import utils

def get_material_template(context):

    # init locals
    mat = {}
    catt_io = context.scene.catt_io

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
    for i_freq, freq in enumerate(catt_io.frequency_bands):

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
        catt_io = context.scene.catt_io

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

        # disable use nodes (easier to access diffuse colour that way)
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
#         catt_io = context.scene.catt_io

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


from bpy_extras.io_utils import ImportHelper
from bpy.props import (StringProperty, BoolProperty)

class MESH_OT_catt_import(Operator, ImportHelper):
    """Import geometry and materials from .GEO file"""

    # init locals
    bl_idname = "catt.import"
    bl_label = "Catt Import"

    # filter files visible in loading popup
    filter_glob: StringProperty( default='*.GEO;*.geo;', options={'HIDDEN'} )
    # some_boolean: BoolProperty( name='Do a thing', description='Do a thing with the file you\'ve selected', default=True)


    def execute(self, context):
        """ method called from ui """

        # parse data from geo file
        [vertices, faces, materials, is_error_detected] = utils.parse_geo_file(self.filepath)
        if( is_error_detected ):
            self.report({'ERROR'}, 'Look into the console for more info')

        # create objects from parsed data
        filename, extension = os.path.splitext( os.path.basename(self.filepath) )
        collection_name = filename
        utils.create_objects_from_parsed_geo_file(vertices, faces, materials, collection_name)

        # convert materials to catt materials
        for material_name, material in materials.items():

            # init locals
            mat = bpy.data.materials[ material_name ]
            mat_template = get_material_template(context)
            rna_dict = {}

            # loop over material properties, assign default
            for key, value in mat_template.items():
                if key not in mat: mat[key] = value["default"]
                rna_dict[key] = value

            # apply rna
            mat["_RNA_UI"] = rna_dict

            # update values based on material abs/scat/etc.
            for i_freq in range(len(material['absorption'])):
                mat['abs_{0}'.format(i_freq)] = material['absorption'][i_freq]
                mat['dif_{0}'.format(i_freq)] = material['diffraction'][i_freq]

            mat['is_diff_estimate'] = material['is_diff_estimate']
            mat['diff_estimate'] = material['diff_estimate']

        return {'FINISHED'}


class MESH_OT_catt_export_room(Operator):
    """Export objects of every collection included in the View Layer to .GEO file"""

    # init locals
    bl_idname = "catt.export_room"
    bl_label = "Catt Export Room"

    def execute(self, context):
        """ method called from ui """

        # init local
        catt_io = context.scene.catt_io

        # update deprecated materials if need be
        self.update_deprecated_catt_materials(context)

        # get list of objects to export (meshes visible in viewport)
        # objects = [obj for obj in bpy.context.view_layer.objects if obj.visible_get() and obj.type == 'MESH']

        # get list of objects in room collection
        collection = bpy.data.collections[catt_io.room_collection]
        objects = utils.get_all_objects_recursive(collection, bpy.context.view_layer)

        # filter only mesh objects
        objects = [obj for obj in objects if obj.type == 'MESH']

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
        export_path = bpy.path.abspath(catt_io.export_path)
        file_name = catt_io.room_file_name
        file_path = os.path.join(export_path, file_name)

        # export objects
        self.export_objects(file_path, objects)

        # exit
        self.report({'INFO'}, 'Room export complete')
        return {'FINISHED'}


    def update_deprecated_catt_materials(self, context):
        """Update properties of all catt materials to latest version"""

        # init locals
        catt_io = context.scene.catt_io
        mat_template = get_material_template(context)

        # loop over materials in scene
        for mat in bpy.data.materials:

            # discard if not a catt material
            if "is_catt_material" not in mat: continue

            # ignore materials without rna (e.g. default dot stroke)
            if not "_RNA_UI" in mat: continue

            # copy rna
            rna_dict = mat["_RNA_UI"]

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
        catt_io = bpy.context.scene.catt_io
        objects_copy = []

        for i_obj, obj in enumerate(objects):

            # debug log
            if catt_io.debug: print('copying objects {0}/{1}: {2}'.format(i_obj+1, len(objects), obj.name))

            # duplicate object
            obj_copy = obj.copy()
            obj_copy.data = obj_copy.data.copy() # make sure object data is not linked to original
            bpy.context.collection.objects.link(obj_copy)

            # apply transform, triangulate, apply modifiers
            bm = utils.bmesh_copy_from_object(obj, transform=False, triangulate=catt_io.triangulate_faces, apply_modifiers=catt_io.apply_modifiers)

            # copy back bmesh to mesh data
            bm.to_mesh(obj_copy.data)
            obj_copy.data.update()
            bm.free()

            # save to locals
            objects_copy.append(obj_copy)

        # is there a join operation to apply?
        if catt_io.merge_objects and len(objects_copy) > 1:

            # debug log
            if catt_io.debug: print('merging objects')

            # Deselect everything
            bpy.ops.object.select_all(action='DESELECT')

            # Select all objects to prepare join operation
            for obj in objects_copy:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = objects_copy[0]

            # join objects, get result
            bpy.ops.object.join()
            concat_object = objects_copy[0]

            # remove duplicate vertices
            if catt_io.rm_duplicates_dist > 0:

                # debug
                if catt_io.debug: print('merging neighbour vertices')

                # merge using bmesh
                bm = bmesh.new()
                bm.from_mesh(concat_object.data)
                bmesh.ops.remove_doubles(bm, verts = bm.verts, dist = catt_io.rm_duplicates_dist)
                bm.to_mesh(concat_object.data)
                concat_object.data.update()
                bm.free()

            # save to locals
            objects_copy = [concat_object]

        # build list of materials used in objects (unique)
        materials_to_export = []
        for obj in objects_copy:
            [materials_to_export.append(mat) for mat in obj.data.materials]

        # remove duplicate materials
        materials_to_export = list(set(materials_to_export))

        # open file
        with open(file_path, 'w', newline='\r\n') as data:

            # init write
            fw = data.write

            # header
            fw('; File generated by the blender catt export add-on from .blend file: \n')
            fw('; {0} \n\n\n'.format(bpy.data.filepath))

            # header from embedded script
            if( catt_io.editor_scripts in bpy.data.texts.keys() ):

                # header
                fw('; COMMENTS \n')
                fw('; (generated from embedded script: {0}) \n\n'.format(catt_io.editor_scripts))

                # get text
                text = bpy.data.texts[catt_io.editor_scripts]

                # write line as catt comment
                for line in text.lines: fw('; ' + line.body + '\n')
                fw('\n\n')

            # materials
            fw('; MATERIALS \n\n')
            r = 1 # round factor

            # loop over materials
            for i_mat, mat in enumerate(materials_to_export):

                # debug log
                if catt_io.debug: print('exporting materials {0}/{1}: {2} '.format(i_mat+1, len(materials_to_export), mat.name))

                # absorption
                fw("abs {0} = <{1} {2} {3} {4} {5} {6} : {7} {8}>".format(utils.mat_name_to_str(mat.name), round(mat['abs_0'], r), round(mat['abs_1'], r), round(mat['abs_2'], r), round(mat['abs_3'], r), round(mat['abs_4'], r), round(mat['abs_5'], r), round(mat['abs_6'], r), round(mat['abs_7'], r)))

                # diffraction
                if mat["use_diffraction"]:

                    fw(" L ")

                    if mat['is_diff_estimate']:

                        fw("<estimate({0})>".format(round(mat['diff_estimate'], 3)))

                    else:

                        fw("<{0} {1} {2} {3} {4} {5} : {6} {7}>".format(round(mat['dif_0'], r), round(mat['dif_1'], r), round(mat['dif_2'], r), round(mat['dif_3'], r), round(mat['dif_4'], r), round(mat['dif_5'], r), round(mat['dif_6'], r), round(mat['dif_7'], r)))

                # colour
                fw(" {{{0} {1} {2}}} \n".format(int(255*mat.diffuse_color[0]), int(255*mat.diffuse_color[1]), int(255*mat.diffuse_color[2])))

            fw('\n\n')

            # vertices header
            fw('CORNERS \n\n')

            # init locals
            vertex_index_offsets = [0]
            faces_index_offsets = [0]

            # loop over objects (but first)
            for obj in objects_copy[:-1]:

                # incr. vertices offsets (to prevent vertex id overwrite)
                vertex_index_offsets.append( len(obj.data.vertices) + vertex_index_offsets[-1])
                faces_index_offsets.append( len(obj.data.polygons) + faces_index_offsets[-1] )

            # loop over objects
            for i_obj, obj in enumerate(objects_copy):

                # debug log
                if catt_io.debug: print('exporting vertices {0}/{1}: {2} '.format(i_obj+1, len(objects_copy), obj.name))

                # loop over vertices
                for vertice in obj.data.vertices:

                    # get vertex coords (absolute)
                    coords = (obj.matrix_world @ vertice.co)

                    # write line
                    index = vertice.index + vertex_index_offsets[i_obj] + 1
                    fw("{0} {1:.2f} {2:.2f} {3:.2f} \n".format(index, coords[0], coords[1], coords[2]) )

            fw('\n\n')

            # faces header
            fw('PLANES\n\n')

            for i_obj, obj in enumerate(objects_copy):

                # get handle to original object (for original name and collection access)
                # warning: may misbehave with merging option
                obj_original = objects[i_obj]

                # debug log
                if catt_io.debug: print('exporting faces {0}/{1}: {2} '.format(i_obj+1, len(objects_copy), obj_original.name))

                # loop over faces
                for i_face, face in enumerate(obj.data.polygons):

                    # init locals
                    # had to use original object here (otherwise copy doesn't belong to any collection)
                    collection_name = '' if len(obj_original.users_collection) == 0 else obj_original.users_collection[0].name
                    material_name = utils.mat_name_to_str(obj.material_slots[face.material_index].material.name)
                    object_name = obj_original.name

                    # auto edge diffraction if collection or object names end with '*'
                    edge_diffraction_str = ''
                    if( len(collection_name) > 0 and collection_name[-1] == '*' ):

                        edge_diffraction_str = '*'
                        collection_name = collection_name.rstrip('*')

                    if object_name[-1] == '*':

                        object_name = object_name.rstrip('*')
                        edge_diffraction_str = '*'

                    # shape face name from collection and object names
                    # 'Master Collection' is the name of blender root collection
                    face_name = object_name

                     # keep original face id (no offset here)
                    if catt_io.export_face_ids: face_name = "{0}-{1}".format(face_name, face.index)
                    if collection_name not in ('', 'Master Collection'): face_name = "{0}-{1}".format(collection_name, face_name)

                    # get face vertices ids
                    offset = vertex_index_offsets[i_obj] + 1
                    vertices_list = [vertice + offset for vertice in face.vertices]
                    vertices_list_str = ' '.join(map(str, vertices_list))

                    # write face line
                    offset = faces_index_offsets[i_obj] + 1
                    fw("[ {0} {1} / {2} / {3}{4} ]\n".format(face.index + offset, face_name, vertices_list_str, material_name, edge_diffraction_str) )

        # loop over objects to remove
        for i_obj, obj in enumerate(objects_copy):
            if catt_io.debug: print('deleting copied objects {0}/{1}: {2} '.format(i_obj+1, len(objects_copy), obj.name))
            bpy.data.objects.remove(obj)

        # return
        if catt_io.debug: print('file saved to: {0}'.format(file_path))

        return 0


class MESH_OT_catt_export_receiver_animation(Operator):
    """Export objects along animated path"""

    # init locals
    bl_idname = "catt.export_receiver_animation"
    bl_label = "Catt Export Animation"

    def execute(self, context):
        """ method called from ui """

        # init local
        scene = context.scene
        catt_io = context.scene.catt_io
        round_factor = 2 # round factor applied on values
        obj = scene.objects[catt_io.receiver_object]

        # open output file
        export_path = bpy.path.abspath(catt_io.export_path)
        file_name = catt_io.receiver_file_name
        file_path = os.path.join(export_path, file_name)
        file = open(file_path,'w')

        # add header
        file.write("RECEIVERS \r\n")

        # sample positions along animations
        [list_translation, list_rotation_euler] = utils.sample_animation_path(context, obj, catt_io.receiver_dist_thresh)

        # loop over positions
        for iPos in range(0, len(list_translation)):

            # init locals
            obj_id = iPos + 1
            loc = list_translation[iPos]

            # shape line
            s = ""
            s += f'{obj_id:02}' + " "
            s += str(round(loc[0], round_factor)) + " " + str(round(loc[1], round_factor)) + " " + str(round(loc[2], round_factor)) + " "

            # WARNING: if you add rotation/euler export, sample_animation_path removes duplicates (even far away duplicates animation wise). Might want to alleviate that depending on export scenarios.
            # rot = obj.rotation_euler
            # s += str(round(rot.x,r)) + " " + str(round(rot.y,r)) + " " + str(round(rot.z,r))

            # write to file
            s += "\r\n"
            file.write(s)

        # write to file
        if catt_io.debug: print('file saved to:', file_path)
        file.close()

        self.report({'INFO'}, "Receiver export complete")
        return {'FINISHED'}


class MESH_OT_catt_export_source_animation(Operator):
    """Export objects along animated path"""

    # init locals
    bl_idname = "catt.export_source_animation"
    bl_label = "Catt Export Animation"

    def execute(self, context):
        """ method called from ui """

        # init local
        scene = context.scene
        catt_io = context.scene.catt_io
        round_factor = 2 # round factor applied on values
        obj = scene.objects[catt_io.source_object]

        # open output file
        export_path = bpy.path.abspath(catt_io.export_path)
        file_name = catt_io.source_file_name
        file_path = os.path.join(export_path, file_name)
        file = open(file_path,'w')

        # sample positions along animations
        [list_translation, list_rotation_euler] = utils.sample_animation_path(context, obj, catt_io.source_dist_thresh)

        # get list of available source names
        source_names = utils.get_catt_source_names()

        # discard if too many positions compared to available source names
        if( len(list_translation) > len(source_names) ):

            file.write("ERROR: too many source positions to export, not enough valid CATT source names")
            file.close()
            self.report({'WARNING'}, "Source export aborted")
            return {'FINISHED'}

        # loop over positions
        for iPos in range(0, len(list_translation)):

            # source header
            file.write("SOURCE " + source_names[iPos] + "\r\n")

            # source pos
            loc = list_translation[iPos]
            s = "  "
            s += "POS = "
            s += str(round(loc[0], round_factor)) + " " + str(round(loc[1], round_factor)) + " " + str(round(loc[2], round_factor))
            s += " \r\n"
            file.write(s)

            # # source aim pos
            # s = "  "
            # s += "AIMPOS = "
            # aimpos = mathutils.Vector([0, 0, 0])
            # s += str(round(aimpos.x, round_factor)) + " " + str(round(aimpos.y, round_factor)) + " " + str(round(aimpos.z, round_factor))
            # s += " \r\n"
            # file.write(s)

            file.write("END \r\n \r\n")

        # write to file
        if catt_io.debug: print('file saved to:', file_path)
        file.close()

        self.report({'INFO'}, "Source export complete")
        return {'FINISHED'}


class MESH_OT_catt_export_receiver_collection(Operator):
    """Export all objects in collection"""

    # init locals
    bl_idname = "catt.export_receiver_collection"
    bl_label = "Catt Export Collection"

    def execute(self, context):
        """ method called from ui """

        # init local
        scene = context.scene
        catt_io = context.scene.catt_io
        round_factor = 2 # round factor applied on values
        collection = bpy.data.collections[catt_io.receiver_collection]

        # open output file
        export_path = bpy.path.abspath(catt_io.export_path)
        file_name = catt_io.receiver_file_name
        file_path = os.path.join(export_path, file_name)
        file = open(file_path,'w')

        # add header
        file.write("RECEIVERS \r\n")

        # init loop over objects
        obj_id = 0

        # get sorted list (alphabetical, as displayed in outliner)
        obj_list = collection.objects[:]
        obj_list.sort(key=lambda obj: obj.name)

        # loop over objects in collection
        for obj in obj_list:

            # init locals
            loc = obj.matrix_world.translation

            # shape line
            s = ""
            s += f'{obj_id:02}' + " "
            s += str(round(loc.x, round_factor)) + " " + str(round(loc.y, round_factor)) + " " + str(round(loc.z, round_factor)) + " "

            # write to file
            s += "\r\n"
            file.write(s)

            # increment counters
            obj_id += 1

        # write to file
        if catt_io.debug: print('file saved to:', filePath)
        file.close()

        self.report({'INFO'}, "Receiver export complete")
        return {'FINISHED'}


class MESH_OT_catt_export_source_collection(Operator):
    """Export all objects in collection"""

    # init locals
    bl_idname = "catt.export_source_collection"
    bl_label = "Catt Export Collection"

    def execute(self, context):
        """ method called from ui """

        # init local
        scene = context.scene
        catt_io = context.scene.catt_io
        round_factor = 2 # round factor applied on values
        collection = bpy.data.collections[catt_io.source_collection]

        # open output file
        export_path = bpy.path.abspath(catt_io.export_path)
        file_name = catt_io.source_file_name
        file_path = os.path.join(export_path, file_name)
        file = open(file_path,'w')

        # get sorted list (alphabetical, as displayed in outliner)
        obj_list = collection.objects[:]
        obj_list.sort(key=lambda obj: obj.name)

        # loop over objects in collection
        for obj in obj_list:

            # source header
            file.write("SOURCE " + obj.name + "\r\n")

            # source pos
            loc = obj.matrix_world.translation
            s = "  "
            s += "POS = "
            s += str(round(loc.x, round_factor)) + " " + str(round(loc.y, round_factor)) + " " + str(round(loc.z, round_factor))
            s += " \r\n"
            file.write(s)

            # # source aim pos
            # s = "  "
            # s += "AIMPOS = "
            # aimpos = mathutils.Vector([0, 0, 0])
            # s += str(round(aimpos.x, round_factor)) + " " + str(round(aimpos.y, round_factor)) + " " + str(round(aimpos.z, round_factor))
            # s += " \r\n"
            # file.write(s)

            file.write("END \r\n \r\n")

        # write to file
        if catt_io.debug: print('file saved to:', filePath)
        file.close()

        self.report({'INFO'}, "Source export complete")
        return {'FINISHED'}


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
        catt_io = context.scene.catt_io

        # check for non flat faces
        if self.arg == 'check_nonflat_faces':

            # discard if no object selected
            sel_objects = bpy.context.selected_objects
            if( len(sel_objects) == 0 ):
                self.report({'INFO'}, 'No object selected.')
                return {'CANCELLED'}

            # switch to edit mode
            bpy.ops.object.mode_set(mode = 'EDIT')

            # get mesh
            mesh = bpy.context.edit_object.data

            # deselect everything
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

                # set face selected if non-flat
                ngon.select = not all( [abs(distance_point_to_plane(v.co, co, norm)) < planar_tolerance for v in ngon.verts[3:]] )

                # flag at least one non flat face detected
                if ngon.select: has_non_flat_faces = True

            # update mesh
            bmesh.update_edit_mesh(mesh)

            # disable edit mode if no non-flat face detected
            if not has_non_flat_faces:

                bpy.ops.object.mode_set(mode = 'OBJECT')
                self.report({'INFO'}, 'No non-flat face detected.')

            return {'FINISHED'}
