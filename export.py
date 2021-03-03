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

def catt_export_room(context):
    """ Main export method """

    scene = context.scene
    obj = context.active_object
    catt_export = scene.catt_export

    # force object mode to perform export operations
    mode_orig = context.mode
    if mode_orig == 'EDIT_MESH':
        bpy.ops.object.mode_set(mode='OBJECT')


    # perform pre-export operations
    (vertices, faces) = catt_vertices_faces_from_object(obj)
    print("number of faces in exported mesh: {}".format(len(faces)))
    # faces = catt_reorder_faces(vertices, faces)

    # set export paths
    export_path = bpy.path.abspath(catt_export.export_path)
    masterFileName = catt_export.master_file_name + ".GEO"
    masterFilepath = os.path.join(export_path, masterFileName)
    # export file (write)
    err = catt_ascii_write(masterFilepath, vertices, faces, obj, catt_export.triangulate_faces, catt_export.master_file_name)
    print('Catt file exported at {0}'.format(masterFilepath))

    return err


def catt_vertices_faces_from_object(ob, use_mesh_modifiers=False):
    """ Get vertices and faces from object ob """

    # get the editmode data
    ob.update_from_editmode()

    # get the modifiers
    try:
        mesh = ob.to_mesh(bpy.context.scene, use_mesh_modifiers, "PREVIEW")
    except RuntimeError:
        raise StopIteration

    # Apply scale / loc / rot (equivalent to Ctrl+A)
    # WARNING: for now, one has to run the script twice to have the proper scale exported...
    bpy.ops.object.select_all(action='DESELECT')
    ob.select = True
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    # TODO:
    # convert will-be-exported mesh to triangles (accepted in CATT, always in the same plane compared to quadmesh vertices)t

    # mesh.transform(global_matrix * ob.matrix_world)
    # print(ob.matrix_local)
    # print(ob.matrix_world)

    vertices = mesh.vertices
    faces = mesh.polygons

    return (vertices, faces)


def catt_ascii_write(filepath, vertices, faces, obj, triangulate, fileName):
    """ Open new ascii file, write data """

    with open(filepath, 'w') as data:
        fw = data.write

        # Catt related header
        header = ";" + fileName + ".GEO"
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
        for vertice in vertices:
            fw("{0} {1:.2f} {2:.2f} {3:.2f} \r\n".format(vertice.index, vertice.co[0], vertice.co[1], vertice.co[2]) )

        # write planes (faces)
        header = "PLANES"
        fw('\r\n%s\r\n\r\n' % header)
        faceID = 1
        for face in faces:
            planeName = 'wall' # default plane name set in Catt
            try:
                planeMaterial = obj.data.materials[face.material_index].name
            except IndexError:
                print("error: attempt to access material index {}, max is {}".format(face.material_index, len(obj.data.materials)))
                return 1

            # convert list of face vertices to string
            faceVertices = ' '.join(map(str, face.vertices))

            # write face line
            fw("[ {0} {1} / {2} / {3} ]\r\n".format(faceID, planeName, faceVertices, planeMaterial) )

            # incr. face counter
            faceID = faceID + 1

            # if len(face.vertices) == 4:
            #     if not triangulate:
            #         fw("[ {0} {1} / {2} {3} {4} {5} / {6} ]\r\n".format(faceID, planeName, face.vertices[0], face.vertices[1], face.vertices[2], face.vertices[3], planeMaterial) )
            #         faceID = faceID + 1
            #     else: # quads to tris to make sure all vertices of a plane are in the same plane in catt
            #         fw("[ {0} {1} / {2} {3} {4} / {5} ]\r\n".format(faceID, planeName, face.vertices[0], face.vertices[1], face.vertices[2], planeMaterial) )
            #         faceID = faceID + 1
            #         fw("[ {0} {1} / {2} {3} {4} / {5} ]\r\n".format(faceID, planeName, face.vertices[2], face.vertices[3], face.vertices[0], planeMaterial) )
            #         faceID = faceID + 1

            # elif len(face.vertices) == 3:
            #     fw("[ {0} {1} / {2} {3} {4} / {5} ]\r\n".format(faceID, planeName, face.vertices[0], face.vertices[1], face.vertices[2], planeMaterial) )
            #     faceID = faceID + 1
            # else:
            #     print("error: exporter only supports tris and quads, face {} has {} vertices".format(faceID, len(face.vertices)))
            #     return 1

    return 0


# def catt_reorder_faces(vertices, faces):
#     # NOT NEEDED ANYMORE: REMOVE DEFAULT AUDIANCE PLANE IN CATT-Acoustics, its it that needs to be horizontal)
#     # first face in list must be the floor (i.e more or less parallel to xy, min z)

#     # for e in dir(faces[0]): print(e)
#     floor_face = faces[0]
#     norm_z = Vector((0.0,0.0,1.0))

#     face_ID = 0
#     floor_face_ID = face_ID

#     faces_list = [] # fix: had to use a list rather than bpy_prop_collection as reodering impossile (without the internet at least :)

#     for face in faces:
#         faces_list.append(face)

#         if (face.normal*norm_z >= floor_face.normal*norm_z) and (face.center[2] <= floor_face.center[2]):
#             floor_face = face
#             floor_face_ID = face_ID
#         face_ID = face_ID + 1

#     #for f in faces_list: print(f.index)
#     tmp = faces[0]
#     faces_list[0] = faces_list[floor_face_ID]
#     faces_list[floor_face_ID] = tmp
#     #print('')
#     #for f in faces_list: print(f.index)
#     return faces_list
