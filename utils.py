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

import bmesh
import bpy


def freq_to_str(freq):
    """convert float freqency to string"""

    # kHz
    if freq < 1000.0:
        return '{0}Hz'.format(int(freq))

    # Hz
    return '{0}kHz'.format(int(freq/1000.0))


def mat_name_to_str(mat_name):
    """convert string material name to string that will correctly be interpreted by CATT"""

    return mat_name.replace('.', '_')


# method from the Print3D add-on: create a bmesh from an object
# (for triangulation, apply modifiers, etc.)
def bmesh_copy_from_object(obj, transform=True, triangulate=True, apply_modifiers=False):
    """ returns a transformed, triangulated copy of the mesh """

    assert obj.type == 'MESH'

    if apply_modifiers and obj.modifiers:
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

    if transform:
        bm.transform(obj.matrix_world)

    if triangulate:
        bmesh.ops.triangulate(bm, faces=bm.faces)

    return bm


def parse_geo_file(filepath):

    # init locals
    materials = dict()
    vertices = dict()
    faces = dict()
    error_detected = False

    # loop over lines
    with open(filepath, "r") as file_reader:
        for line_id, line in enumerate(file_reader, 1):

            # shape data
            line_split = line.split()

            # discard empty lines
            if( len(line_split) == 0 ): continue

            # debug
            # print(line_split)

            # line: material definition
            if( line_split[0].lower() == 'abs' ):

                # init locals
                nFreq = 8
                material = {'absorption': [0.0]*nFreq, 'diffraction': [0.0]*nFreq, 'color': [0, 0, 0], 'use_diffraction': True, 'is_diff_estimate': False, 'diff_estimate': 0.0}

                # extract data: material name (assumes no spaces)
                material_name = line_split[1]

                # prepare absorption and diffraction extraction
                abs_index_start = line.index('<')
                abs_index_end = line.index('>')
                dif_index_start = line[abs_index_end+1::].index('<') + abs_index_end + 1
                dif_index_end = line[abs_index_end+1::].index('>') + abs_index_end + 1

                # extract data: absorption
                absorption = onlyDigitList( line[abs_index_start:abs_index_end].split() )

                # deal with incomplete absorption definition
                if( len( absorption ) < nFreq ):

                    # pad with last value
                    last_value = absorption[-1]
                    for i in range(nFreq-len( absorption )): absorption.append(last_value)

                    # log error
                    error_detected = True
                    print("\nWARNING: expecting 8 freq. bands absorption definition at line", line_id, "\n-> padding high frequencies with last band value")

                # extract data: store absorption to locals
                material['absorption'] = absorption

                # extract data: diffraction
                diffraction = onlyDigitList( line[dif_index_start:dif_index_end].split() )
                if( dif_index_start == 0 ):

                    # diffraction not defined
                    material['use_diffraction'] = False

                elif( 'estimate' in line[dif_index_start:dif_index_end] ):

                    # material diffraction is defined using catt "estimate(..)" syntax
                    material['is_diff_estimate'] = True
                    material['diff_estimate'] = diffraction[0]

                else:

                    # diffraction is defined using classic (per band) syntax
                    if( len( diffraction ) < nFreq ):

                        # pad with last value
                        last_value = diffraction[-1]
                        for i in range(nFreq-len( diffraction )): diffraction.append(last_value)

                        # log error
                        error_detected = True
                        print("\nWARNING: expecting 8 freq. bands diffraction definition at line", line_id, "\n-> padding high frequencies with last band value")

                    # update locals
                    material['diffraction'] = diffraction

                # color definition
                color = onlyDigitList( line[dif_index_end::].split() )
                color = [round(float(x)/255.0, 3) for x in color]
                color.append(1.0) # alpha
                material['color'] = color

                # save material to locals
                materials[material_name] = material

                # # debug
                # print("material:", material_name, absorption, diffraction, color)

            # line: vertex (corner) definition
            elif( line_split[0].isnumeric() ):

                # extract data
                vertice_id = int( line_split[0] )
                vertice_id -= 1 # start from 0 compared to catt that starts from 1
                vertice_xyz = [float(x) for x in line_split[1:4]]

                # save to locals
                vertices[vertice_id] = {'xyz': vertice_xyz}

                # # debug
                # print("vertex:", vertice_id, vertice_xyz)

            # line: face (plane) definition
            elif( line_split[0][0] == "[" ):

                # check that catt didn't split line in two (... yes, if too long, it does)
                try:
                    index_open = line.index("[")
                    index_close = line.index("]")
                except ValueError:
                    print("\nERROR: Unexpected line break at line", line_id, "\n->", line + "Face import discarded\n")
                    error_detected = True
                    continue

                # shape data
                line_strip = line.replace("[", "").replace("]", "") # .replace("/", "")
                line_split = line_strip.split()

                # deal with object names containing spaces
                index_slash_1 = line_split.index("/")
                index_slash_2 = line_split.index("/", index_slash_1+1, len(line_split)-1)

                # extract data
                face_id = int( line_split[0] )
                obj_name = ' '.join(line_split[1:index_slash_1])
                face_vertices = [int(x)-1 for x in line_split[(index_slash_1+1):index_slash_2]]
                face_material = line_split[-1]

                # deal with automatic edge diffraction syntax
                # ('*' at end of material name, that need to be moved to end of object name to be preserved in blender scene for next export)
                # note: can't use material names with * at the end in original CATT scene
                if( face_material[-1] == '*' ):
                    face_material = face_material[:-1] # remove last character
                    obj_name = obj_name + '*'

                # save to locals
                faces[face_id] = {'obj_name': obj_name, 'vertices': face_vertices, 'material': face_material}

                # # debug
                # print("face: ", face_id, face_name, face_vertices, face_material)

    return [vertices, faces, materials, error_detected]


def onlyDigitList(list_in):

    list_str = [''.join(c for c in x if (c.isdigit() or c =='.')) for x in list_in]
    list_str = list( filter(None, list_str) )
    list_float = [float(x) for x in list_str]

    return list_float


def create_objects_from_parsed_geo_file(vertices, faces, materials, collection_name='catt import'):

    # get list of existing materials
    existing_material_names = [m.name for m in bpy.data.materials]

    # loop over materials
    for material_name in materials.keys():

        # discard if material exists
        if( material_name in existing_material_names ): continue

        # create material
        material = bpy.data.materials.new(name=material_name)

        # set material color (both node and non-node)
        material.use_nodes = True
        bsdf = material.node_tree.nodes["Principled BSDF"]
        material_color = tuple( materials[material_name]['color'] )
        bsdf.inputs["Base Color"].default_value = material_color
        material.diffuse_color = material_color


    # 16:11

    # get list of all the objects to create (from names in faces)
    object_list = {}
    # loop over faces
    for face_id in faces.keys():

        # create object entry in local dict if not already in
        object_name = faces[face_id]['obj_name']
        if( object_name not in object_list ):
            object_list[object_name] = {'vertices': [], 'faces': []}

        # save face / vertice to object
        object_list[object_name]['faces'].append( faces[face_id] )
        object_list[object_name]['vertices'].append( faces[face_id]['vertices'] )


    # make collection
    new_collection = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(new_collection)


    # loop over objects to create
    for object_name in object_list.keys():

        # shape list of materials (unique) of current object
        mesh_materials = [ face['material'] for face in object_list[object_name]['faces'] ]
        mesh_materials = list( dict.fromkeys( mesh_materials ))

        # shape list of vertices (unique) of current object
        vertice_ids = [item for sublist in object_list[object_name]['vertices'] for item in sublist] # from list of lists to flat list
        vertice_ids = list( dict.fromkeys( vertice_ids ) ) # remove duplicates
        vertice_ids.sort() # sort list (to prepare renumbering of vertice ids in faces to span 0:num_vertices
        mesh_vertices = []
        for vertice_id in vertice_ids:
            mesh_vertices.append( tuple( vertices[vertice_id]['xyz'] ) )

        # shape list of faces of current object
        mesh_faces = []
        mesh_faces_materials = []
        face_id = 0
        for face in object_list[object_name]['faces']:

            # add face to local list
            face_vertices = [ vertice_ids.index(vertice_id) for vertice_id in face['vertices'] ]
            mesh_faces.append(face_vertices)

            # add face material id to local list
            mesh_faces_materials.append( mesh_materials.index(face['material']) )

        # create mesh
        new_mesh = bpy.data.meshes.new(object_name + '_mesh')

        # assign vertices and faces to new mesh
        edges = []
        new_mesh.from_pydata(mesh_vertices, edges, mesh_faces)

        # add materials to mesh
        for material_name in mesh_materials:
            new_mesh.materials.append( bpy.data.materials[material_name] )

        # assign materials to mesh faces
        new_mesh.polygons.foreach_set("material_index", tuple( mesh_faces_materials ))

        # update mesh
        new_mesh.update()

        # make object from mesh
        new_object = bpy.data.objects.new(object_name, new_mesh)

        # add object to scene collection
        new_collection.objects.link(new_object)

