"""
Script for fixing WRL imported scenes (exported from CATT). The script will loop over
the materials present in the scene, and rename them based on matching rgb values found
in mat_dict. Fill mat_dict with CATT material name as keys and rgb values matching that
defined in the original CATT scene before running.

WARNING: do not modify the imported scene before running that script (e.g. don't go merging all faces into a single mesh)
"""

import bpy

# check if two tuples are the same (threshold based)
def isEqual(v1, v2):
    thresh = 0.003 # < 1 in 0:255 rgb scale
    if( len(v1) != len(v2) ): return False

    for i in range(0, len(v1)):
        if( abs( v1[i] - v2[i] ) >= thresh ):
             return False

    return True


# define catt materials and associated rgb (prepare factorisation)
mat_dict = dict()
mat_dict['floor'] = {'rgb': [255, 128, 128, 255]}
mat_dict['bigwall'] = {'rgb': [255, 0, 0, 255]}
mat_dict['smallwall'] = {'rgb': [128, 64, 64, 255]}
mat_dict['roof'] = {'rgb': [128, 0, 0, 255]}

# rgb 0-255 to 0-1
for matName in mat_dict:
    mat_dict[matName]['rgb'] = tuple([x/255 for x in mat_dict[matName]['rgb']])

# setup catt materials (create, set rgb, etc.)
existingMatName = [m.name for m in bpy.data.materials]
for matName in mat_dict:

    # create material if need be
    if( not matName in existingMatName ):

        bpy.data.materials.new(name=matName)

        # set diffuse (for looks)
        bpy.data.materials[matName].diffuse_color = mat_dict[matName]['rgb']
        print('created new mat: ', matName)


# loop over objects, replace material (assumed unique) by catt materials based on rgb
for obj in bpy.context.scene.objects:

    # discard if object not a mesh
    if obj.type != 'MESH':
        continue

    # discard if material already processed
    if( obj.data.materials[0].name in mat_dict ):
        continue

    # loop over catt materials (potential replacements)
    isReplaced = False
    for matName in mat_dict:

        # identify match based on rgb
        if isEqual( obj.data.materials[0].diffuse_color, mat_dict[matName]['rgb'] ):

            # replace material
            obj.data.materials[0] = bpy.data.materials[matName]

            # flag replacement
            # print('replaced {} with {}'.format(obj.data.materials[0].name, matName))
            isReplaced = True

            # exit loop
            break

    # warning if no equivalent catt material was found for current material
    if( not isReplaced ):
        print('could not find replacement for material {} with rgb {}'.format(obj.data.materials[0].name, obj.data.materials[0].diffuse_color))