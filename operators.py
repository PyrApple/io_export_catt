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


# create catt material from blender material (simply add abs / diff attributes)
def init_catt_material(mat):

    # flag as catt material
    mat['is_catt_material'] = True

    # loop over frequency bands
    nFreqBands = 8
    for iFreq in range(nFreqBands):
        mat['abs_{0}'.format(iFreq)] = 40.0
        mat['dif_{0}'.format(iFreq)] = 50.0

    # disable use nodes (easier to access diffuse color that way)
    mat.use_nodes = False


class CattMaterialCreate(Operator):

    # init locals
    bl_label = "New Catt Material"
    bl_idname = 'catt.matcreate'
    bl_options = {'REGISTER', 'UNDO'}
    mat_name = bpy.props.StringProperty(name='Material Name', default='CattMat')

    def execute(self, context):

        return {'FINISHED'}

        error = self.sanityCheck(context)
        if not error:
            mat = self.createCattMaterial(context, self.mat_name)
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
        init_catt_material(mat)
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

        init_catt_material(mat)

        return {'FINISHED'}


class CattMaterialRetroCompatibility(Operator):
    """"""
    bl_idname = "catt.convert_catt_material_from_old_to_new"
    bl_label = "Convert to new Catt Material"

    def execute(self, context):

        obj = context.object
        mat = obj.active_material

        mat['is_catt_material'] = mat['cattMaterial']
        del mat['cattMaterial']

        mat.use_nodes = False

        return {'FINISHED'}


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

        # view_layer = bpy.context.scene.view_layers["View Layer"]

        # loop over view layers
        for view_layer in bpy.context.scene.view_layers:

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
                    init_catt_material(mat)
        return error, warning



    def exportRoom(self, collection_names):
        """ Main export method """

        # get locals
        catt_export = bpy.context.scene.catt_export
        export_path = bpy.path.abspath(catt_export.export_path)

        # get export path
        fileName = catt_export.master_file_name + ".GEO"
        filePath = os.path.join(export_path, fileName)

        # get list of objects to export
        objects = self.getObjectsInCollections(collection_names)

        # add collection less objects (todo: not sure this is robust way to identify)
        for obj in bpy.context.scene.objects:
            print(obj.name, len(obj.users_collection), obj.users_collection[0].name)
            if( obj.users_collection[0].name == 'Master Collection' ):
                objects.append(obj)

        # export objects
        self.exportObjects(filePath, objects)

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

        # get list of objects as bmeshes
        bmeshes = dict()
        for obj in objects:
            # get bmesh
            bm = bmesh_copy_from_object(obj, transform=True, triangulate=catt_export.triangulate_faces, apply_modifiers=catt_export.apply_modifiers)
            bmeshes[obj.name] = bm

        # save face info before concat to single bmesh
        bmFacesInfo = []
        for obj in objects:

            # get collection name
            collectionName = ''
            if( len(obj.users_collection) > 0 ):
                collection = obj.users_collection[0] # only support 1st level collections
                collectionName = collection.name

            # loop over faces
            bm = bmeshes[obj.name]
            for face in bm.faces:

                # get mat name
                matName = obj.material_slots[face.material_index].material.name

                # save to locals
                bmFacesInfo.append([collectionName, obj.name, matName])

        # concat into single bmesh
        bm_concat = bmesh.new()
        mesh = bpy.data.meshes.new("mesh")
        for objName in bmeshes:
            bmeshes[objName].to_mesh(mesh)
            bm_concat.from_mesh(mesh)
            bmeshes[objName].free()

        # remove duplicates
        bmesh.ops.remove_doubles(bm_concat, verts=bm_concat.verts, dist=0.001)

        print('required LUT rebuild probably screws the whole collection/obj/mat face referencing above')
        bm_concat.faces.ensure_lookup_table()

        # get list of materials in objects
        materials = dict()
        # loop over objects
        for obj in objects:
            # loop over materials
            for mat in obj.data.materials:
                # add material to locals if not already present
                if mat.name not in materials:
                    materials[mat.name] = mat


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
            for vertice in bm_concat.verts:
                verticeId = vertice.index + 1
                fw("{0} {1:.2f} {2:.2f} {3:.2f} \n".format(verticeId, vertice.co[0], vertice.co[1], vertice.co[2]) )

            # write planes (faces)
            header = "PLANES"
            fw('\n%s\n\n' % header)

            for iFace in range(len(bm_concat.faces)):
            # for face in bm_concat.faces:
                face = bm_concat.faces[iFace]

                # to clean
                collectionName = bmFacesInfo[iFace][0]
                objName = bmFacesInfo[iFace][1]
                matName = bmFacesInfo[iFace][2]

                # auto edge scattering if collection or object names end with '*'
                edgeScatteringStr = ''
                if( len(collectionName) > 0 and collectionName[-1] == '*' ):
                    edgeScatteringStr = '*'
                    collectionName = self.removeTrailingAsterix(collectionName)
                if( objName[-1] == '*' ):
                    objName = self.removeTrailingAsterix(objName)
                    edgeScatteringStr = '*'

                # shape face name collection and object names
                faceName = ''
                if( collectionName != '' ):
                    faceName += collectionName + '-'
                faceName += objName

                # get face vertice ids
                vertList = [vertice.index + 1 for vertice in face.verts]
                vertListStr = ' '.join(map(str, vertList))

                # write face line
                fw("[ {0} {1} / {2} / {3}{4} ]\n".format(face.index + 1, faceName, vertListStr, matName, edgeScatteringStr) )


        bm_concat.free()

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



# # JOIN BMESHES
#
# The best solution I found so far is using the bmesh.from_mesh( mesh ) method.
# Apparently, if you call this method more than once, it will add the 2nd mesh to the first, thus effectively joining them:
#
# import bpy, bmesh
#
# bm = bmesh.new()
# bm.from_mesh( mesh1 ) # Add first mesh
# bm.from_mesh( mesh2 ) # Add 2nd mesh


# # REMOVE BMESH DUPLICATES
# bm = bmesh.new()   # create an empty BMesh
# bm.from_mesh(me)   # fill it in from a Mesh
#
# bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.1)
#
# # Finish up, write the bmesh back to the mesh
# bm.to_mesh(me)
# bm.free()  # free and prevent further access
#
# me.validate()
# me.update()


