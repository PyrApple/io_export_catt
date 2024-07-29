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

# Interface for this addon.

import bpy
from bpy.types import Panel
from . import utils

class View3DCattPanel:
    """ common panel """

    # init locals
    bl_category = "Catt"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    @classmethod
    def poll(cls, context):
        """ define context when to display the addon panel """
        return True


class VIEW3D_PT_catt_info(View3DCattPanel, Panel):
    """ panel information """

    # title
    bl_label = "Info"

    def draw(self, context):
        """ method called upon ui draw """

        # init locals
        layout = self.layout
        catt_io = context.scene.catt_io

        row = layout.row()
        row.label(text="- Assign CATT materials")

        row = layout.row()
        row.label(text="- Check normal orientations")

        row = layout.row()
        row.label(text="- Assert flat faces (or triangulate)")


class VIEW3D_PT_catt_main(View3DCattPanel, Panel):
    """ panel main """

    # title
    bl_label = "Catt"

    def draw(self, context):
        """ method called upon ui draw """

        # init locals
        layout = self.layout
        catt_io = context.scene.catt_io
        ui_elmt_offset = 0.6

        # Globals
        box = layout.box()
        box.label(text="Preferences", icon="PREFERENCES")

        row = box.row()
        row.prop(catt_io, "export_path")

        row = box.row()
        row.prop(catt_io, "debug")

        # Room import/export
        box = layout.box()
        box.label(text="Room", icon="CUBE")

        row = box.row()
        row.operator("catt.import", text="Import Room", icon='IMPORT')
        row.ui_units_y += 1 + ui_elmt_offset

        row = box.row()
        row.prop(catt_io, "room_file_name")

        row = box.row()
        row.prop(catt_io, "editor_scripts")

        row.ui_units_y += 1 + ui_elmt_offset

        row = box.row(align=True)
        row.operator("catt.utils", text="Detect Non-Planar faces", icon="XRAY").arg = 'check_nonflat_faces' # 'SURFACE_DATA', 'XRAY', 'MOD_WARP'

        row = box.row(align=True)
        row.prop(catt_io, "triangulate_faces")

        row = box.row(align=True)
        row.prop(catt_io, "apply_modifiers")

        row = box.row(align=True)
        row.prop(catt_io, "export_face_ids")

        row = box.row(align=True)
        row.prop(catt_io, "merge_objects")

        row = box.row(align=True)
        row.enabled = catt_io.merge_objects
        row.prop(catt_io, "rm_duplicates_dist")

        row.ui_units_y += 1 + ui_elmt_offset

        row = box.row(align=True)
        row.operator("catt.export_room", text="Export Room", icon='EXPORT')

        # row = col.row(align=True)
        # row.prop(catt_io, "export_progress", slider=True)
        # row.enabled = False


        # Receiver export
        box = layout.box()
        box.label(text="Receiver", icon="MONKEY")

        row = box.row()
        row.prop(catt_io, "receiver_file_name")

        row = box.row(align=True)
        row.prop(catt_io, "receiver_export_type")

        if( catt_io.receiver_export_type == "COLLECTION"):

            row = box.row(align=True)
            row.prop_search(catt_io, "receiver_collection", bpy.data, "collections")

            row = box.row(align=True)
            row.operator("catt.export_receiver_collection", text="Export", icon='EXPORT')

        else:

            row = box.row(align=True)
            row.prop_search(catt_io, "receiver_object", bpy.data, "objects")

            row = box.row(align=True)
            row.prop(catt_io, "receiver_dist_thresh")

            row = box.row(align=True)
            op = row.operator("catt.export_receiver_animation", text="Export", icon='EXPORT')
            # op.prop_type = "source"


class VIEW3D_PT_catt_material(View3DCattPanel, Panel):
    """ panel material """

    # title
    bl_label = "Material"

    def draw(self, context):
        """ method called upon ui draw """

        # init locals
        layout = self.layout
        obj = context.active_object
        catt_io = context.scene.catt_io

        # discard if no object selected
        if not obj:
            return

        # material datablock manager
        box = layout.row()
        layout.template_ID_preview(obj, "active_material")

        # if object has materials
        if len(context.active_object.material_slots) > 0:

            # discard if object has no active material
            mat = obj.active_material
            if not mat:
                return

            # # retro compatibility
            # if 'cattMaterial' in mat:
            #     box = layout.row()
            #     box.label(text="Deprecated CATT material", icon='ERROR')
            #     return

            # material is not a catt material
            if 'is_catt_material' not in mat:

                box = layout.row()
                box.label(text="Not a CATT material", icon='ERROR')

                box = layout.row()
                box.operator("catt.convert_to_catt_material", text="Convert to CATT material")

                return

            # # retro compatibility
            # if 'use_diffraction' not in mat:
            #     box = layout.row()
            #     box.label(text="Deprecated CATT material", icon='ERROR')
            #     box = layout.row()
            #     box.operator("catt.convert_catt_material_from_old_to_new", text="Convert to new CATT material")
            #     return

            # define absorption coefficients
            box = layout.row()
            box.label(text="Absorption")

            # loop over frequencies
            for i_freq, freq in enumerate(catt_io.frequency_bands):
                row = layout.row(align=True)
                row.label(text=utils.freq_to_str(freq))
                row.prop(mat,'["abs_{0}"]'.format(i_freq), text="")

            # empty space
            box = layout.row(align=True)
            box.label(text="")

            # define diffraction coefficients
            box = layout.row()
            box.label(text="Diffraction")

            # use diffraction?
            row = layout.row(align=True)
            split = row.split(factor=0.7)
            colsub = split.column()
            colsub.label(text="Use Diffraction")
            colsub = split.column()
            colsub.prop(mat,'["use_diffraction"]', text="")

            # discard remainder if not use diffraction
            if not mat['use_diffraction']:
                return

            # use estimate?
            row = layout.row(align=True)
            split = row.split(factor=0.7)
            colsub = split.column()
            colsub.label(text="Use Estimated")
            colsub = split.column()
            colsub.prop(mat,'["is_diff_estimate"]', text="")

            if( mat['is_diff_estimate'] ):
                row = layout.row(align=True)
                row.label(text="estimated")
                row.prop(mat,'["diff_estimate"]', text="")
            else:
                # loop over frequencies
                for i_freq, freq in enumerate(catt_io.frequency_bands):
                    row = layout.row(align=True)
                    row.label(text=utils.freq_to_str(freq))
                    row.prop(mat,'["dif_{0}"]'.format(i_freq), text="")

