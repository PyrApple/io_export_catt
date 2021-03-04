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

import bmesh
from bpy.types import Panel
from . import report

class CattExportToolBar:
    bl_label = "CattExport"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    _type_to_icon = {
        bmesh.types.BMVert: 'VERTEXSEL',
        bmesh.types.BMEdge: 'EDGESEL',
        bmesh.types.BMFace: 'FACESEL',
        }

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    @staticmethod
    def draw_report(layout, context):
        """Display Reports"""
        info = report.info()
        if info:
            obj = context.edit_object

            layout.label("Output:")
            box = layout.box()
            col = box.column(align=False)
            # box.alert = True
            for i, (text, data) in enumerate(info):
                if obj and data and data[1]:
                    bm_type, bm_array = data
                    col.operator("mesh.print3d_select_report",
                                 text=text,
                                 icon=CattExportToolBar._type_to_icon[bm_type]).index = i
                else:
                    col.label(text)

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        catt_export = scene.catt_export
        obj = context.object

        row = layout.row()
        row.label("Compatibility Check:")

        # TODO: Automatize check with operators --------------------
        # col = layout.column(align=True)
        # col.prop(catt_export, "display_normals", text="Display Room Normals")

        #if (catt_export.display_normals == True):
        # me = obj.data
        # if obj.mode == 'EDIT':
        #     me = obj.data
        #     me.show_normal_face = catt_export.display_normals
        #     print('Object EDITE')
        # if context.mode == 'EDIT_MESH':
        #     print('CONTEXT EDITE')
            # obj.show_normal_face = catt_export.display_normals

        # scene.tool_settings.normal_size = 1.0

        # rowsub = col.row(align=True)
        # rowsub.operator("catt.not_implemented", text="Make Consistent")
        # rowsub.operator("catt.not_implemented", text="Flip Normals")
        # col = layout.column(align=True)
        # col.operator("catt.not_implemented", text="Check Flat Surfaces")
        # col = layout.column(align=True)
        # col.operator("catt.not_implemented", text="Apply Scale")
        # -----------------------------------------------------------
        # Meanwhile: simple stepwise description --------------------
        row = layout.row()
        row.label("1. Make Normals consistent")
        row = layout.row()
        row.label("2. Make Normals point inwards")
        # row = layout.row()
        # row.label("3. Apply scale (Ctrl+A)")
        row = layout.row()
        row.label("3. Check all faces are flat, else use triangulate option")
        # -----------------------------------------------------------

        col = layout.column(align=True)
        col.label('')
        
        rowsub = col.row(align=True)
        rowsub.prop(catt_export, "triangulate_faces", text="Triangulate faces")
        rowsub = col.row(align=True)
        rowsub.prop(catt_export, "apply_modifiers", text="Apply modifiers")
        
        col = layout.column(align=True)
        col.label('')

        col = layout.column()
        rowsub = col.row(align=True)
        rowsub.label("Export Path:")
        # rowsub.prop(catt_export, "use_apply_scale", text="", icon='MAN_SCALE')
        # rowsub.prop(catt_export, "use_export_texture", text="", icon='FILE_IMAGE')
        rowsub = col.row()
        rowsub.prop(catt_export, "export_path", text="")
        

        rowsub = col.row(align=True)
        rowsub.label("Exported .GEO file name:")
        rowsub = col.row()
        rowsub.prop(catt_export, "master_file_name", text="")

        rowsub = col.row(align=True)
        # rowsub.prop(catt_export, "export_format", text="")
        rowsub.operator("catt.export_room", text="Export active object", icon='EXPORT')

        CattExportToolBar.draw_report(layout, context)

        col = layout.column(align=True)
        col.label('')
        col = layout.column(align=True)
        col.label('Custom Material:')

        # bail on wrong display mode
        if context.scene.game_settings.material_mode != 'GLSL':
            row = layout.row()
            row.label('CattMaterial requires GLSL mode', icon='ERROR')
            row = layout.row()
            row.prop(context.scene.game_settings, 'material_mode', text='')
            return

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
                    row.label('Not a CATT Material', icon='ERROR')
                    row = layout.row()
                    row.operator("catt.convert_to_catt_material", text="Convert to Catt Material")
                        # signaled_as_non_catt_material = True
                else:

                    row = layout.row()
                    row.label("Absorption:")
                    # col = layout.column(align=True)
                    rowsub = layout.row(align=True)
                    rowsub.label("125Hz")
                    rowsub.prop(mat,'["abs_0"]', text="")
                    rowsub = layout.row(align=True)
                    rowsub.label("250Hz")
                    rowsub.prop(mat,'["abs_1"]', text="")
                    rowsub = layout.row(align=True)
                    rowsub.label("500Hz")
                    rowsub.prop(mat,'["abs_2"]', text="")
                    rowsub = layout.row(align=True)
                    rowsub.label("1kHz")
                    rowsub.prop(mat,'["abs_3"]', text="")
                    rowsub = layout.row(align=True)
                    rowsub.label("2kHz")
                    rowsub.prop(mat,'["abs_4"]', text="")
                    rowsub = layout.row(align=True)
                    rowsub.label("4kHz")
                    rowsub.prop(mat,'["abs_5"]', text="")
                    rowsub = layout.row(align=True)
                    rowsub.label("8kHz")
                    rowsub.prop(mat,'["abs_6"]', text="")
                    rowsub = layout.row(align=True)
                    rowsub.label("16kHz")
                    rowsub.prop(mat,'["abs_7"]', text="")

                    row = layout.row(align=True)
                    row.label('')
                    row = layout.row()
                    row.label("Diffraction:")
                    # col = layout.column(align=True)
                    rowsub = layout.row(align=True)
                    rowsub.label("125Hz")
                    rowsub.prop(mat,'["dif_0"]', text="")
                    rowsub = layout.row(align=True)
                    rowsub.label("250Hz")
                    rowsub.prop(mat,'["dif_1"]', text="")
                    rowsub = layout.row(align=True)
                    rowsub.label("500Hz")
                    rowsub.prop(mat,'["dif_2"]', text="")
                    rowsub = layout.row(align=True)
                    rowsub.label("1kHz")
                    rowsub.prop(mat,'["dif_3"]', text="")
                    rowsub = layout.row(align=True)
                    rowsub.label("2kHz")
                    rowsub.prop(mat,'["dif_4"]', text="")
                    rowsub = layout.row(align=True)
                    rowsub.label("4kHz")
                    rowsub.prop(mat,'["dif_5"]', text="")
                    rowsub = layout.row(align=True)
                    rowsub.label("8kHz")
                    rowsub.prop(mat,'["dif_6"]', text="")
                    rowsub = layout.row(align=True)
                    rowsub.label("16kHz")
                    rowsub.prop(mat,'["dif_7"]', text="")


class CattExportToolBarObject(Panel, CattExportToolBar):
    bl_category = "CATT Export"
    bl_context = "objectmode"

# So we can have a panel in both object mode and editmode
class CattExportToolBarMesh(Panel, CattExportToolBar):
    bl_category = "CATT Export"
    bl_context = "mesh_edit"
