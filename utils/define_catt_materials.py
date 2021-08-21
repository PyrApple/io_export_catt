"""
Script for adjusting absorption, etc. properties of CATT materials present in the scene
Fill mat_dict with CATT material name as keys and values matching that defined in the
original CATT scene as values.
"""

import bpy

# define catt materials and associated rgb (prepare factorisation)
mat_dict = dict()
mat_dict['floor'] = {'abs': [ 1, 1, 1, 2, 2, 2 ], 'estimate': 0.01}
mat_dict['bigwall'] = {'abs': [ 2, 3.2, 4, 5, 6.4, 7 ], 'estimate': 0.03}
mat_dict['smallwall'] = {'abs': [ 2, 3.2, 4, 5, 6.4, 7 ], 'estimate': 0.03}
mat_dict['roof'] = {'abs': [ 2, 3.2, 4, 5, 6.4, 7 ], 'dif': [30, 40, 50, 60, 70, 80]}

# select dummy object for active material swap
bpy.context.view_layer.objects.active = bpy.context.scene.objects['Todelete']

# loop over materials
for mat in bpy.data.materials:

    # if material should be processed
    if( mat.name in mat_dict):

        print('processing material: {0}'.format(mat.name))

        # if not catt material
        if 'is_catt_material' not in mat:

            # set active material (required for operator)
            bpy.context.object.active_material = mat

            # invoque operator
            bpy.ops.catt.convert_to_catt_material()
            print('convert {0} to catt material'.format(mat.name))

        # init locals
        num_freq_bands = 8

        # setup absorption
        for i_freq in range(num_freq_bands):

            # copy last available value if not specified freq band
            if len(mat_dict[mat.name]['abs']) <= i_freq:
                v = mat_dict[mat.name]['abs'][-1]
            else:
                v = mat_dict[mat.name]['abs'][i_freq]

            # assign
            mat['abs_{0}'.format(i_freq)] = v

        # setup diffusion
        if 'estimate' in mat_dict[mat.name]:
            mat['is_diff_estimate'] = True
            mat['diff_estimate'] = mat_dict[mat.name]['estimate']
        else:
            for i_freq in range(num_freq_bands):

                # copy last available value if not specified freq band
                if len(mat_dict[mat.name]['dif']) <= i_freq:
                    v = mat_dict[mat.name]['dif'][-1]
                else:
                    v = mat_dict[mat.name]['dif'][i_freq]

                # assign
                mat['dif_{0}'.format(i_freq)] = v