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
import bmesh

from . import report


class View3DCattPanel:
    bl_category = "Catt"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    @classmethod
    def poll(cls, context):

        obj = context.active_object
        if( obj is None ): return True
        if( obj.mode in {'OBJECT', 'EDIT'} ): return True
        return False
        # return obj is not None and obj.type == 'MESH' and obj.mode in {'OBJECT', 'EDIT'}


class VIEW3D_PT_catt_instructions(View3DCattPanel, Panel):
    bl_label = "Instructions"

    def draw(self, context):
        layout = self.layout

        # TODO: Automatize check with operators
        # Meanwhile: simple stepwise description
        row = layout.row()
        row.label(text="- Make Normals consistent")
        row = layout.row()
        row.label(text="- Make Normals point inwards")
        # row = layout.row()
        # row.label("3. Apply scale (Ctrl+A)")
        row = layout.row()
        row.label(text="- Check all faces are flat, else use triangulate option")
        row = layout.row()
        row.label(text="- Only supports single depth collections")
        row = layout.row()
        row.label(text="- Add * to the end of an object name to flag it for automatic edge scattering in Catt")
        row = layout.row()
        row.label(text="- Add * to the end of a collection name to flag all its objects for automatic edge scattering in Catt")


class VIEW3D_PT_catt_export(View3DCattPanel, Panel):
    bl_label = "Export"

    def draw(self, context):

        layout = self.layout
        catt_export = context.scene.catt_export

        col = layout.column(align=True)

        rowsub = col.row(align=True)
        rowsub.prop(catt_export, "triangulate_faces")

        rowsub = col.row(align=True)
        rowsub.prop(catt_export, "apply_modifiers")

        rowsub = col.row(align=True)
        rowsub.prop(catt_export, "individual_geo_files")

        col = layout.column()
        rowsub = col.row(align=True)
        rowsub.label(text="Export Path:")
        # rowsub.prop(catt_export, "use_apply_scale", text="", icon='MAN_SCALE')
        rowsub = col.row()
        rowsub.prop(catt_export, "export_path", text="")


        rowsub = col.row(align=True)
        rowsub.label(text="Exported .GEO file name:")
        rowsub = col.row()
        rowsub.prop(catt_export, "master_file_name", text="")

        rowsub = col.row(align=True)
        # rowsub.prop(catt_export, "export_format", text="")
        rowsub.operator("catt.export_room", text="EXPORT", icon='EXPORT')


class VIEW3D_PT_catt_materials(View3DCattPanel, Panel):
    bl_label = "Materials"

    def draw(self, context):
        layout = self.layout

        catt_export = context.scene.catt_export
        obj = context.object

        # # bail on wrong display mode
        # if context.scene.game_settings.material_mode != 'GLSL':
        #     row = layout.row()
        #     row.label(text="CattMaterial requires GLSL mode", icon='ERROR')
        #     row = layout.row()
        #     row.prop(context.scene.game_settings, 'material_mode', text='')
        #     return

        # bail on no object (We don't want to use poll because that hides the panel)
        if not obj:
            return

        # material datablock manager
        row = layout.row()
        layout.template_ID_preview(obj, "active_material", new="catt.matcreate")

        # material editor
        row = layout.row()
        # signaled_as_non_catt_material = False

        # for materialSlot in context.active_object.material_slots:

        if len(context.active_object.material_slots) > 0:

            # mat = materialSlot.material
            mat = obj.active_material
            # print(mat.name)

            # bail code
            if mat:
                if 'cattMaterial' not in mat:
                    # if not signaled_as_non_catt_material:
                    row.label(text="Not a CATT Material", icon='ERROR')
                    row = layout.row()
                    row.operator("catt.convert_to_catt_material", text="Convert to Catt Material")
                        # signaled_as_non_catt_material = True
                else:

                    row = layout.row()
                    row.label(text="Absorption:")
                    # col = layout.column(align=True)
                    rowsub = layout.row(align=True)
                    rowsub.label(text="125Hz")
                    rowsub.prop(mat,'["abs_0"]', text="")
                    rowsub = layout.row(align=True)
                    rowsub.label(text="250Hz")
                    rowsub.prop(mat,'["abs_1"]', text="")
                    rowsub = layout.row(align=True)
                    rowsub.label(text="500Hz")
                    rowsub.prop(mat,'["abs_2"]', text="")
                    rowsub = layout.row(align=True)
                    rowsub.label(text="1kHz")
                    rowsub.prop(mat,'["abs_3"]', text="")
                    rowsub = layout.row(align=True)
                    rowsub.label(text="2kHz")
                    rowsub.prop(mat,'["abs_4"]', text="")
                    rowsub = layout.row(align=True)
                    rowsub.label(text="4kHz")
                    rowsub.prop(mat,'["abs_5"]', text="")
                    rowsub = layout.row(align=True)
                    rowsub.label(text="8kHz")
                    rowsub.prop(mat,'["abs_6"]', text="")
                    rowsub = layout.row(align=True)
                    rowsub.label(text="16kHz")
                    rowsub.prop(mat,'["abs_7"]', text="")

                    row = layout.row(align=True)
                    row.label(text="")
                    row = layout.row()
                    row.label(text="Diffraction:")
                    # col = layout.column(align=True)
                    rowsub = layout.row(align=True)
                    rowsub.label(text="125Hz")
                    rowsub.prop(mat,'["dif_0"]', text="")
                    rowsub = layout.row(align=True)
                    rowsub.label(text="250Hz")
                    rowsub.prop(mat,'["dif_1"]', text="")
                    rowsub = layout.row(align=True)
                    rowsub.label(text="500Hz")
                    rowsub.prop(mat,'["dif_2"]', text="")
                    rowsub = layout.row(align=True)
                    rowsub.label(text="1kHz")
                    rowsub.prop(mat,'["dif_3"]', text="")
                    rowsub = layout.row(align=True)
                    rowsub.label(text="2kHz")
                    rowsub.prop(mat,'["dif_4"]', text="")
                    rowsub = layout.row(align=True)
                    rowsub.label(text="4kHz")
                    rowsub.prop(mat,'["dif_5"]', text="")
                    rowsub = layout.row(align=True)
                    rowsub.label(text="8kHz")
                    rowsub.prop(mat,'["dif_6"]', text="")
                    rowsub = layout.row(align=True)
                    rowsub.label(text="16kHz")
                    rowsub.prop(mat,'["dif_7"]', text="")