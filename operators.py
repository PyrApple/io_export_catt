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
from bpy.props import (
        StringProperty,
        BoolProperty,
        IntProperty,
        FloatProperty,
        FloatVectorProperty,
        EnumProperty,
        PointerProperty,
        )


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


class CattMaterialCreate(Operator):
    """Create an catt material"""
    bl_label = "New Catt Material"
    bl_idname = 'catt.matcreate'
    bl_options = {'REGISTER', 'UNDO'}

    MatName = bpy.props.StringProperty(name='Material Name', default='CattMat')

    def execute(self, context):
        error = self.sanityCheck(context)
        if not error:
            mat = self.createCattMaterial(context, self.MatName)
            self.assignMaterial(context, mat)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, error)
            return {'CANCELLED'}

    # assign material to all selected objects, overriding all mat slots
    def assignMaterial(self, context, mat):
        for obj in context.selected_objects:
            # obj.data.materials.clear()
            obj.data.materials.append(mat)

    def createCattMaterial(self, context, name):
        mat = bpy.data.materials.new(name)
        catt_setMaterialProps(mat)
        return mat

    # returns error if selected objects has usable materials
    def sanityCheck(self, context):

        for obj in context.selected_objects:
            if obj.type != 'MESH':
                return 'Object is not a mesh, Aborted'
            for mat in obj.data.materials:
                if mat:
                    return False
                    return 'Object already has materials, Aborted.'
        return False


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


class CattExportRoom(Operator):
    """Export active object as catt room"""
    bl_idname = "catt.export_room"
    bl_label = "Catt Export"

    def execute(self, context):
        # scene = bpy.context.scene
        # catt_export = scene.catt_export
        # from . import export

        # Check if export possible
        error = ''
        warning = ''
        ret = 0

        # get list of collections to export
        collection_names = self.getActiveCollectionNames()

        # check that each object in selected collection has catt materials
        for collection_name in collection_names:
            collection = bpy.data.collections[collection_name]
            for obj in collection.objects:
                if obj.type == 'MESH':
                    error, warning = self.checkForCattMaterials(obj)

                    if warning:
                        self.report({'WARNING'}, warning)

                    if error:
                        self.report({'ERROR'}, error)
                        return {'CANCELLED'}

        # export collections
        err = self.exportRoom(collection_names)

        if err == 0:
            self.report({'INFO'}, 'Catt export complete')
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, 'Catt export aborted, check in the console for more details')
            return {'CANCELLED'}


    # return the list of enabled collection names
    def getActiveCollectionNames(self):

        # init locals
        collection_names = []
        view_layer = bpy.context.scene.view_layers["View Layer"]

        # loop over collections
        for layer_collection in view_layer.layer_collection.children:

            # add collection to list if not disabled
            if not layer_collection.exclude:
                collection_names.append(layer_collection.name)

        return collection_names


    # check that object has catt materials attached
    def checkForCattMaterials(self, obj):

        error = ''
        warning = ''

        if len(obj.data.materials) == 0:
            error = 'Room must have at least one material'
        # when object has no material, somehow obj.data.materials still contains
        # "<bpy_collection[1], IDMaterials>" which is of NoneType
        elif len(obj.data.materials) == 1 and obj.data.materials[0] is None:
            error = 'Room must have at least one material'
        else:
            for mat in obj.data.materials:
                if 'abs_0' not in mat:
                    warning = obj.name + ' has at least 1 non Catt material: setting default abs/diff values'
                    catt_setMaterialProps(mat)
        return error, warning



    def exportRoom(self, collection_names):
        """ Main export method """

        # get locals
        catt_export = bpy.context.scene.catt_export
        export_path = bpy.path.abspath(catt_export.export_path)

        if not catt_export.individual_geo_files:

            # get export path
            fileName = catt_export.master_file_name + ".GEO"
            filePath = os.path.join(export_path, fileName)

            # get list of objects to export
            objects = self.getObjectsInCollections(collection_names)

            # export objects
            self.exportObjects(filePath, objects)

        else:

            for collectionName in collection_names:

                # get export path
                fileName = self.removeTrailingAsterix(collectionName) + ".GEO"
                filePath = os.path.join(export_path, fileName)

                # get list of objects to export
                objects = self.getObjectsInCollections([collectionName])

                # export objects
                self.exportObjects(filePath, objects)

            # write main file
            fileName = catt_export.master_file_name + ".GEO"
            filePath = os.path.join(export_path, fileName)
            self.writeImporterFile(filePath, collection_names)

        return 0

    # remove * from collection name if need be
    def removeTrailingAsterix(self, name):

        if( name[-1] == '*' ):
            return name[0:len(name) - 1]
        else:
            return name


    #
    def writeImporterFile(self, filePath, collection_names):


        # open file
        with open(filePath, 'w', newline='\r\n') as data:

            fw = data.write

            # Catt related header
            header = ";" + filePath
            fw('%s\n' % header)
            header = ";PROJECT="
            fw('%s\n\n' % header)

            # Blender Add-on related header
            header = ";FILE GENERATED VIA BLENDER CATT EXPORT ADD-ON"
            fw('%s\n' % header)
            blendFilename = os.path.splitext(os.path.split(bpy.data.filepath)[1])[0]
            if not blendFilename:
                blendFilename = 'floating file (unsaved)'
            else:
                blendFilename = blendFilename + ".blend"
            header = ";BASED ON .BLEND FILE: " + blendFilename
            fw('%s\n\n' % header)

            for collectionName in collection_names:
                fw('INCLUDE %s\n' % self.removeTrailingAsterix(collectionName))


    # return a list of objects in collections
    def getObjectsInCollections(self, collection_names):

        # init local
        objects = []

        # loop over collections
        for collection_name in collection_names:

            # get collection from name
            collection = bpy.data.collections[collection_name]

            # loop over objects
            for obj in collection.objects:
                if obj.type == 'MESH':
                    objects.append(obj)

        return objects


    def exportObjects(self, filePath, objects):

        # init locals
        catt_export = bpy.context.scene.catt_export

        # get list of materials in objects
        materials = dict()
        # loop over objects
        for obj in objects:
            # loop over materials
            for mat in obj.data.materials:
                # add material to locals if not already present
                if mat.name not in materials:
                    materials[mat.name] = mat

        # get list of objects as bmeshes
        bmeshes = dict()
        for obj in objects:
            # get bmesh
            bm = bmesh_copy_from_object(obj, transform=True, triangulate=catt_export.triangulate_faces, apply_modifiers=catt_export.apply_modifiers)
            bmeshes[obj.name] = bm


        # open file
        with open(filePath, 'w', newline='\r\n') as data:

            fw = data.write

            # Catt related header
            header = ";" + filePath
            fw('%s\n' % header)
            header = ";PROJECT="
            fw('%s\n\n' % header)

            # Blender Add-on related header
            header = ";FILE GENERATED VIA BLENDER CATT EXPORT ADD-ON"
            fw('%s\n' % header)
            blendFilename = os.path.splitext(os.path.split(bpy.data.filepath)[1])[0]
            if not blendFilename:
                blendFilename = 'floating file (unsaved)'
            else:
                blendFilename = blendFilename + ".blend"
            header = ";BASED ON .BLEND FILE: " + blendFilename
            fw('%s\n\n' % header)

            # write material(s)
            header = ""
            r = 1 # round factor
            for mat in materials.values():
                tmp = "abs {0} = <{1} {2} {3} {4} {5} {6} : {7} {8} > L < {9} {10} {11} {12} {13} {14} : {15} {16}> {{{17} {18} {19}}} \n".format(mat.name, round(mat['abs_0'], r), round(mat['abs_1'], r), round(mat['abs_2'], r), round(mat['abs_3'], r), round(mat['abs_4'], r), round(mat['abs_5'], r), round(mat['abs_6'], r), round(mat['abs_7'], r), round(mat['dif_0'], r), round(mat['dif_1'], r), round(mat['dif_2'], r), round(mat['dif_3'], r), round(mat['dif_4'], r), round(mat['dif_5'], r), round(mat['dif_6'], r), round(mat['dif_7'], r), int(100*mat.diffuse_color[0]), int(100*mat.diffuse_color[1]), int(100*mat.diffuse_color[2]))
                header = header + tmp
            fw('%s\n' % header)


            # write corners (vertices)
            header = "CORNERS"
            fw('%s\n\n' % header)
            idOffset = 0
            vertIdOffsets = dict()
            for objName in bmeshes:
                bm = bmeshes[objName]
                for vertice in bm.verts:
                    verticeId = vertice.index + 1 + idOffset # as catt expects ids starting from 1
                    fw("{0} {1:.2f} {2:.2f} {3:.2f} \n".format(verticeId, vertice.co[0], vertice.co[1], vertice.co[2]) )

                vertIdOffsets[objName] = idOffset
                idOffset += len(bm.verts)


            # todo: keep track of vertices idOffset, to be taken into account in faces definition below

            # write planes (faces)
            header = "PLANES"
            fw('\n%s\n\n' % header)
            idOffset = 0
            for objName in bmeshes:
                bm = bmeshes[objName]
                obj = bpy.data.objects[objName]

                hasAutoEdgeScattering = False
                if( obj.name[-1] == '*'): hasAutoEdgeScattering = True
                if( len(obj.users_collection) > 0 ):
                    collection = obj.users_collection[0] # only support 1st level collections
                    if( collection.name[-1] == '*'): hasAutoEdgeScattering = True

                edgeScatteringStr = ''
                if( hasAutoEdgeScattering ): edgeScatteringStr = '*'

                for face in bm.faces:

                    # get face material
                    matName = obj.material_slots[face.material_index].material.name

                    # get face vertice ids
                    vertList = [vertice.index + 1 + vertIdOffsets[objName] for vertice in face.verts]
                    vertListStr = ' '.join(map(str, vertList))

                    # write face line
                    planeName = 'wall' # default plane name set in Catt
                    fw("[ {0} {1} / {2} / {3}{4} ]\n".format(face.index + 1 + idOffset, 'wall', vertListStr, matName, edgeScatteringStr) )

                idOffset += len(bm.faces)

        print('Catt file exported at {0}'.format(filePath))
        return 0


import bmesh

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
