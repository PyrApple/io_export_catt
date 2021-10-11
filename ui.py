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

from bpy.types import Panel
from . import utils

class View3DCattPanel:
    """ common panel """

    # init locals
    bl_category = "CATT"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    @classmethod
    def poll(cls, context):
        """ define context when to display the addon panel """
        return True


class VIEW3D_PT_catt_instruction(View3DCattPanel, Panel):
    """ panel utilities """

    # title
    bl_label = "Utilities"

    def draw(self, context):
        """ method called upon ui draw """

        # init locals
        layout = self.layout

        row = layout.row()
        row.label(text="Assign CATT materials")

        row = layout.row()
        row.label(text="Check normal orientations")

        row = layout.row()
        row.label(text="Assert flat faces (or triangulate)")

        row = layout.row()
        row.operator("catt.utils", text="Detect Non-Planar faces", icon="XRAY").arg = 'check_nonflat_faces' # 'SURFACE_DATA', 'XRAY', 'MOD_WARP'


class VIEW3D_PT_catt_export(View3DCattPanel, Panel):
    """ panel export """

    # title
    bl_label = "Export"

    def draw(self, context):
        """ method called upon ui draw """

        # init locals
        layout = self.layout
        catt_export = context.scene.catt_export

        col = layout.column(align=True)

        # rowsub = col.row(align=True)
        # rowsub.label(text="Path And File Name")

        rowsub = col.row()
        rowsub.prop(catt_export, "export_path", text="")

        # rowsub = col.row(align=True)
        # rowsub.label(text="Exported .GEO file name:")

        rowsub = col.row()
        rowsub.prop(catt_export, "master_file_name", text="")

        rowsub = col.row()
        rowsub.label(text="")

        rowsub = col.row(align=True)
        rowsub.prop(catt_export, "triangulate_faces")

        rowsub = col.row(align=True)
        rowsub.prop(catt_export, "apply_modifiers")

        rowsub = col.row()
        rowsub.label(text="")
        rowsub = col.row(align=True)
        rowsub.label(text="Remove doubles:")
        rowsub = col.row(align=True)
        rowsub.prop(catt_export, "rm_duplicates_dist")

        rowsub = col.row()
        rowsub.label(text="")

        rowsub = col.row(align=True)
        rowsub.operator("catt.export", text="Export", icon='EXPORT')


class VIEW3D_PT_catt_material(View3DCattPanel, Panel):
    """ panel material """

    # title
    bl_label = "Material"

    def draw(self, context):
        """ method called upon ui draw """

        # init locals
        layout = self.layout
        obj = context.object
        catt_export = context.scene.catt_export

        # discard if no object selected
        if not obj:
            return

        # material datablock manager
        row = layout.row()
        layout.template_ID_preview(obj, "active_material")

        # if object has materials
        if len(context.active_object.material_slots) > 0:

            # discard if object has no active material
            mat = obj.active_material
            if not mat:
                return

            # retro compatibility
            if 'cattMaterial' in mat:
                row = layout.row()
                row.label(text="Deprecated CATT material", icon='ERROR')
                return

            # material is not a catt material
            if 'is_catt_material' not in mat:

                row = layout.row()
                row.label(text="Not a CATT material", icon='ERROR')

                row = layout.row()
                row.operator("catt.convert_to_catt_material", text="Convert to CATT material")

                return

            # retro compatibility
            if 'use_diffraction' not in mat:
                row = layout.row()
                row.label(text="Deprecated CATT material (missing use_diffraction property)", icon='ERROR')
                row = layout.row()
                row.operator("catt.convert_catt_material_from_old_to_new", text="Convert to new CATT material")
                return

            # define absorption coefficients
            row = layout.row()
            row.label(text="Absorption")

            # loop over frequencies
            for i_freq, freq in enumerate(catt_export.frequency_bands):
                rowsub = layout.row(align=True)
                rowsub.label(text=utils.freq_to_str(freq))
                rowsub.prop(mat,'["abs_{0}"]'.format(i_freq), text="")

            # empty space
            row = layout.row(align=True)
            row.label(text="")

            # define diffraction coefficients
            row = layout.row()
            row.label(text="Diffraction")

            # use diffraction?
            rowsub = layout.row(align=True)
            split = rowsub.split(factor=0.7)
            colsub = split.column()
            colsub.label(text="Use Diffraction")
            colsub = split.column()
            colsub.prop(mat,'["use_diffraction"]', text="")

            # discard remainder if not use diffraction
            if not mat['use_diffraction']:
                return

            # use estimate?
            rowsub = layout.row(align=True)
            split = rowsub.split(factor=0.7)
            colsub = split.column()
            colsub.label(text="Use Estimated")
            colsub = split.column()
            colsub.prop(mat,'["is_diff_estimate"]', text="")

            if( mat['is_diff_estimate'] ):
                rowsub = layout.row(align=True)
                rowsub.label(text="estimated")
                rowsub.prop(mat,'["diff_estimate"]', text="")
            else:
                # loop over frequencies
                for i_freq, freq in enumerate(catt_export.frequency_bands):
                    rowsub = layout.row(align=True)
                    rowsub.label(text=utils.freq_to_str(freq))
                    rowsub.prop(mat,'["dif_{0}"]'.format(i_freq), text="")

