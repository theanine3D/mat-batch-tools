import mathutils
import bpy
from bpy.utils import(register_class, unregister_class)
from bpy.types import(Panel, PropertyGroup)
from bpy.props import(StringProperty,
                      FloatProperty, BoolProperty)

bl_info = {
    "name": "Material Batch Tools",
    "description": "Batch tools for quickly modifying, copying, and pasting nodes on all materials in selected objects",
    "author": "Theanine3D",
    "version": (0, 1),
    "blender": (3, 4, 0),
    "category": "Material",
    "location": "Properties -> Material Properties",
    "support": "COMMUNITY"
}


# PROPERTY DEFINTIONS
bake_node_preset = {
    "image": "",
    "interpolation": "Linear",
    "projection": "FLAT",
    "projection_blend": 0.0,
    "extension": "REPEAT",
    "name": "Bake Target Node"
}


class MatBatchProperties(bpy.types.PropertyGroup):
    BakeTargetNodeColorEnable: bpy.props.BoolProperty(
        name="Enable", description="Enable or disable the optional color decoration for the Bake Target Node", default=True)
    BakeTargetNodeColor: bpy.props.FloatVectorProperty(
        name="Color", subtype="COLOR", description="Color to use for the Bake Target Node. This is purely cosmetic - it just makes the node easier to find", default=(0.52, 0.145, 0.152), size=3, min=0, max=1)
    UVMapNodeTarget: bpy.props.StringProperty(
        name="UV Map", description="Name of the UV map to set in the UV Map node", default="UVMap", maxlen=64)
    UVMapNodeExtensionFilter: bpy.props.StringProperty(
        name="Filter", description="Only the Image Texture nodes that are set to this file format will be modified", default="PNG", maxlen=20)
    UVSlotIndex: bpy.props.EnumProperty(
        name="UV Slot", description="The UV Slot that will be modified by the buttons below", items=[("1", 'UV Slot 1', 'The first UV slot in the object mesh(es)', 1), ("2", 'UV Slot 2', 'The second UV slot in the object mesh(es)', 2)], default=1)
    VCName: bpy.props.StringProperty(
        name="Name", description="Name to set in Vertex Color slot 1", default="Col", maxlen=64)
    AlphaBlendMode: bpy.props.EnumProperty(
        name="Blend Mode", description="The Blend Mode and Shadow Mode to set in the material(s). If set to Alpha Blend, Shadow Mode will be set to Alpha Clip", items=[("OPAQUE", 'Opaque', 'No transparency', 0), ("CLIP", 'Alpha Clip', 'Pixels will be either 100 percent transparent or 100 percent opaque', 1), ("BLEND", 'Alpha Blend', 'Pixels will be anywhere between 0 to 100 percent transparent', 2)], default=0)
    AlphaBlendFilter: bpy.props.EnumProperty(
        name="Filter", description="Only materials that satisfy this filter will be modified", items=[("NOFILTER", 'None', 'No filter. All materials will be modified', 0), ("PRINCIPLEDNODE", 'Principled BSDF Alpha', 'There must be a Principled node in the material, and its "Alpha" input is either connected to another node or is less than 1.000', 1), ("TRANSPARENTNODE", 'Transparent BSDF', 'There must be at least one Transparent BSDF in the material', 2)], default=0)
    AlphaThreshold: bpy.props.FloatProperty(
        name="Clip Threshold", subtype="FACTOR", description="This setting is used only by Alpha Clip", default=0.5, min=0.0, max=1.0)


# FUNCTION DEFINITIONS

def recursive_node_search(startnode, end_node_type):
    '''Searches into a node's links for a specific node type. Search ends if a node of the specified type is found, or if .'''
    endnode = None
    connecting_nodes = list()

    for x in range(0, 5, 1):
        for i in startnode.inputs:
            if len(startnode.inputs) >= (x + 1):
                for l in startnode.inputs[x].links:
                    connecting_nodes.append(
                        startnode.inputs[x].links[x].from_node)
            else:
                break

    while endnode == None:
        for x in range(0, 5, 1):
            for n in connecting_nodes:
                for i in n.inputs:
                    if len(startnode.inputs) >= (x + 1):
                        if len(n.inputs[x].links) > 0:
                            for l in n.inputs[x].links:
                                if n.inputs[x].links[x].from_node.type == end_node_type:
                                    endnode = n.inputs[x].links[x].from_node
                                    return endnode
                                else:
                                    connecting_nodes.append(
                                        n.inputs[x].links[x].from_node)
                        else:
                            continue

                connecting_nodes.remove(n)

        if len(connecting_nodes) < 2:
            if len(connecting_nodes) < 1:
                return None
            elif len(connecting_nodes[0].inputs.links) < 1:
                return None
            else:
                continue


# Bake Target copy button


class CopyBakeTargetNode(bpy.types.Operator):
    """Copy the currently active Image Texture node and set it as a preset for baking."""
    bl_idname = "material.copy_bake_target"
    bl_label = "Copy"
    bl_options = {'REGISTER'}

    def execute(self, context):

        # Check if there's actually an active object and active material
        if bpy.context.active_object is not None and bpy.context.active_object.active_material is not None:
            if len(bpy.context.active_object.material_slots) is not 0:
                if len(bpy.context.active_object.active_material.node_tree.nodes) is not 0:
                    # Check if there's an active node
                    if bpy.context.active_object.active_material.node_tree.nodes.active != None:
                        # Check if the selected, active node is actually an Image Texture.
                        if bpy.context.active_object.active_material.node_tree.nodes.active.type != "TEX_IMAGE":
                            # Add an error message below if not an Image Texture
                            pass
                        else:
                            if bpy.context.active_object.active_material.node_tree.nodes.active.image != None:
                                bake_node_preset["image"] = bpy.context.active_object.active_material.node_tree.nodes.active.image.name
                                bake_node_preset["interpolation"] = bpy.context.active_object.active_material.node_tree.nodes.active.interpolation
                                bake_node_preset["projection"] = bpy.context.active_object.active_material.node_tree.nodes.active.projection
                                bake_node_preset["projection_blend"] = bpy.context.active_object.active_material.node_tree.nodes.active.projection_blend
                                bake_node_preset["extension"] = bpy.context.active_object.active_material.node_tree.nodes.active.extension

        return {'FINISHED'}


# Bake Target paste button

class PasteBakeTargetNode(bpy.types.Operator):
    """Paste the Bake Target Node in all materials in selected objects, using the node settings previously copied with Copy button"""
    bl_idname = "material.paste_bake_target"
    bl_label = "Paste"
    bl_options = {'REGISTER'}

    def execute(self, context):

        list_of_mats = set()

        # Check if any objects are selected.
        if len(bpy.context.selected_objects) > 0:
            # Check if an image texture has actually been copied yet, and if there's an active material actually selected
            if bake_node_preset["image"] != "":

                # For each selected object
                for obj in bpy.context.selected_objects:

                    for mat in obj.material_slots.keys():
                        if mat != '':
                            list_of_mats.add(mat)

                    # For each material in selected object
                    for mat in list_of_mats:

                        # Check if there's actually a material in the material slot
                        if mat is not '':

                            # Find Material Output node
                            reference_node = None
                            for node in bpy.data.materials[mat].node_tree.nodes:
                                if node.type == "OUTPUT_MATERIAL":
                                    reference_node = node
                                    break

                            # If no Material Output node exists, look for an alternative reference node instead
                            if reference_node is None:
                                for node in bpy.data.materials[mat].node_tree.nodes:
                                    if node.type == "BSDF_PRINCIPLED" or node.type == "EMISSION":
                                        reference_node = node
                                        break

                            # If reference node was found:
                            if reference_node is not None:

                                new_image_node = None
                                bake_target_exists = False

                                # Check if Bake Target Node already exists. If so, reset it.
                                for node in bpy.data.materials[mat].node_tree.nodes:
                                    node.select = False
                                    if "Bake Target Node" in node.name:
                                        new_image_node = node
                                        bake_target_exists = True
                                        break

                                if not bake_target_exists:
                                    # Create Image Texture node if Bake Target Node doesn't already exist
                                    new_image_node = bpy.data.materials[mat].node_tree.nodes.new(
                                        'ShaderNodeTexImage')

                                new_image_node.image = bpy.data.images[bake_node_preset["image"]]
                                new_image_node.location = mathutils.Vector(
                                    ((reference_node.location[0] + 180), (reference_node.location[1])))
                                new_image_node.interpolation = bake_node_preset["interpolation"]
                                new_image_node.projection = bake_node_preset["projection"]
                                new_image_node.projection_blend = bake_node_preset["projection_blend"]
                                new_image_node.extension = bake_node_preset["extension"]
                                new_image_node.color = bpy.context.scene.MatBatchProperties.BakeTargetNodeColor
                                new_image_node.use_custom_color = bpy.context.scene.MatBatchProperties.BakeTargetNodeColorEnable

                                new_image_node.name = "Bake Target Node"
                                new_image_node.label = "Bake Target"
                                new_image_node.select = True
                                bpy.data.materials[mat].node_tree.nodes.active = new_image_node

        return {'FINISHED'}


# Bake Target delete button

class DeleteBakeTargetNode(bpy.types.Operator):
    """Delete the Bake Target Node, if present, in all materials in selected objects"""
    bl_idname = "material.delete_bake_target"
    bl_label = "Delete"
    bl_options = {'REGISTER'}

    def execute(self, context):
        list_of_mats = set()

        # Check if any objects are selected
        if len(bpy.context.selected_objects) > 0:
            # Check if an image texture has actually been copied yet
            if bake_node_preset["image"] != "":

                # For each selected object
                for obj in bpy.context.selected_objects:
                    for mat in obj.material_slots.keys():
                        if mat != '':
                            list_of_mats.add(mat)

                    # For each material in selected object
                    for mat in list_of_mats:
                        if mat != '':
                            # Check if Bake Target Node already exists. If so, delete it.
                            for node in bpy.data.materials[mat].node_tree.nodes:
                                if "Bake Target Node" in node.name:
                                    bpy.data.materials[mat].node_tree.nodes.remove(
                                        node)
                                    break

        return {'FINISHED'}

# Assign UV Map Node button


class AssignUVMapNode(bpy.types.Operator):
    """Assign a UV Map node to any Image Texture that satisfies the entered Filter, in all materials in selected objects"""
    bl_idname = "material.assign_uv_map_node"
    bl_label = "Assign UV Map Node"
    bl_options = {'REGISTER'}

    def execute(self, context):
        mats = set()

        # Check if any objects are selected
        if len(bpy.context.selected_objects) > 0:

            # For each selected object
            for obj in bpy.context.selected_objects:
                for mat in obj.material_slots.keys():
                    if mat is not '':
                        mats.add(mat)

                # For each material in selected object
                for mat in mats:

                    nodetree = bpy.data.materials[mat].node_tree
                    links = bpy.data.materials[mat].node_tree.links

                    if mat != '':
                        # Look for Image Texture nodes
                        for node in nodetree.nodes:
                            new_UV_node = None
                            reference_node = None

                            if node.type == "TEX_IMAGE" and node.image:

                                # Check if Image Texture is in the user's entered format
                                if node.image.file_format == bpy.context.scene.MatBatchProperties.UVMapNodeExtensionFilter:

                                    # Check if Image Texture already has a node connected to it
                                    if node.inputs[0].links:

                                        # If node connected to it is a UV Map node...
                                        if node.inputs[0].links[0].from_node.type == "UVMAP":

                                            # Delete the old UV Map node
                                            nodetree.nodes.remove(
                                                node.inputs[0].links[0].from_node)
                                            reference_node = node

                                        # If the Image Texture has some other kind of node connected... recurvsively search to find the closest UV Map node
                                        else:
                                            foundnode = recursive_node_search(
                                                node, "UVMAP")
                                            if foundnode:
                                                reference_node = foundnode.outputs[0].links[0].to_node
                                                nodetree.nodes.remove(
                                                    foundnode)
                                            else:
                                                reference_node = node
                                    else:
                                        reference_node = node

                                    # Create new UV Map node
                                    new_UV_node = nodetree.nodes.new(
                                        "ShaderNodeUVMap")
                                    new_UV_node.name = "Batch UV Map"
                                    new_UV_node.uv_map = bpy.context.scene.MatBatchProperties.UVMapNodeTarget
                                    new_UV_node.location = mathutils.Vector(
                                        ((reference_node.location[0] - 200), (reference_node.location[1] - 150)))
                                    nodetree.links.new(
                                        new_UV_node.outputs["UV"], reference_node.inputs[0])

        return {'FINISHED'}


# Overwrite UV Slot Name button

class OverwriteUVSlotName(bpy.types.Operator):
    """Using the specified UV Map name above, this button will overwrite the name of the UV Map in the specified UV slot, in all selected objects. If UV Map slot doesn't exist, a new UV Map will be created with that name"""
    bl_idname = "object.overwrite_uv_slot_name"
    bl_label = "Overwrite UV Slot Name"
    bl_options = {'REGISTER'}

    def execute(self, context):

        # Check if any objects are selected
        if len(bpy.context.selected_objects) > 0:

            # For each selected object
            for obj in bpy.context.selected_objects:
                mesh = obj.data
                uvslots = mesh.uv_layers
                uvslot_index = int(
                    bpy.context.scene.MatBatchProperties.UVSlotIndex)
                uvname = bpy.context.scene.MatBatchProperties.UVMapNodeTarget

                counter = 0
                for slot in uvslots:
                    if slot.name == uvname:
                        if counter != uvslot_index - 1:
                            slot.name = slot.name + ".001"
                    else:
                        counter += 1

                if len(uvslots) == 0 and uvslot_index == 1:
                    uvslots.new(
                        name=uvname)
                elif len(uvslots) == 1 and uvslot_index == 2:
                    uvslots.new(
                        name=uvname)
                elif len(uvslots) == 0 and uvslot_index == 2:
                    uvslots.new(
                        name=uvname + ".001")
                    uvslots.new(
                        name=uvname)
                elif uvslots[uvslot_index-1] is not None:
                    uvslots[uvslot_index -
                            1].name = uvname

        return {'FINISHED'}


# Set UV Slot as Active button

class SetUVSlotAsActive(bpy.types.Operator):
    """Sets the currently selected UV Slot above as the 'active' slot in all selected objects. Does not modify the UV map name"""
    bl_idname = "object.set_uv_slot_as_active"
    bl_label = "Set UV Slot as Active"
    bl_options = {'REGISTER'}

    def execute(self, context):

        # Check if any objects are selected
        if len(bpy.context.selected_objects) > 0:

            # For each selected object
            for obj in bpy.context.selected_objects:
                mesh = obj.data
                uvslots = mesh.uv_layers
                uvslot_index = int(
                    bpy.context.scene.MatBatchProperties.UVSlotIndex)
                if len(uvslots) > 0:
                    uvslots.active = uvslots[uvslot_index - 1]

        return {'FINISHED'}

# Assign Vertex Color to Nodes


class AssignVCToNodes(bpy.types.Operator):
    """Assign the Vertex Color name above to all Color Attribute nodes, in all materials in selected objects"""
    bl_idname = "material.assign_vc_to_nodes"
    bl_label = "Assign Name to Color Nodes"
    bl_options = {'REGISTER'}

    def execute(self, context):
        mats = set()

        # Check if any objects are selected
        if len(bpy.context.selected_objects) > 0:

            # For each selected object
            for obj in bpy.context.selected_objects:
                for mat in obj.material_slots.keys():
                    if mat is not '':
                        mats.add(mat)

                # For each material in selected object
                for mat in mats:
                    for node in bpy.data.materials[mat].node_tree.nodes:
                        if node.type == "VERTEX_COLOR":
                            node.layer_name = bpy.context.scene.MatBatchProperties.VCName
        return {'FINISHED'}

# Rename Vertex Color Slot button


class RenameVertexColorSlot(bpy.types.Operator):
    """Renames the first Vertex Color slot in all selected objects, using the name specified above"""
    bl_idname = "object.rename_vertex_color"
    bl_label = "Rename Vertex Color Slot 1"
    bl_options = {'REGISTER'}

    def execute(self, context):

        # Check if any objects are selected
        if len(bpy.context.selected_objects) > 0:

            # For each selected object
            for obj in bpy.context.selected_objects:
                mesh = obj.data
                vcslots = mesh.color_attributes
                vcname = bpy.context.scene.MatBatchProperties.VCName

                if len(vcslots) > 0:
                    vcslots[0].name = vcname
                else:
                    vcslots.new(name=vcname, type="FLOAT_COLOR",
                                domain="POINT")
        return {'FINISHED'}


# Set Blend Mode button

class SetBlendMode(bpy.types.Operator):
    """Sets the currently selected Blend Mode above as the Blend & Shadow Mode in all materials, in all selected objects"""
    bl_idname = "material.set_blend_mode"
    bl_label = "Set Blend Mode"
    bl_options = {'REGISTER'}

    def execute(self, context):
        alpha_mode = bpy.context.scene.MatBatchProperties.AlphaBlendMode
        shadow_mode = bpy.context.scene.MatBatchProperties.AlphaBlendMode
        filter_mode = bpy.context.scene.MatBatchProperties.AlphaBlendFilter
        alpha_threshold = bpy.context.scene.MatBatchProperties.AlphaThreshold
        if alpha_mode == "BLEND":
            shadow_mode = "CLIP"

        list_of_mats = set()

        # Check if any objects are selected
        if len(bpy.context.selected_objects) > 0:

            # For each selected object
            for obj in bpy.context.selected_objects:

                for mat in obj.material_slots.keys():
                    if mat != '':
                        list_of_mats.add(mat)

                # For each material in selected object
                for mat in list_of_mats:

                    # Check if there's actually a material in the material slot
                    if mat is not '':

                        # Filter 1 - Principled BSDF with Alpha
                        if filter_mode == "PRINCIPLEDNODE":
                            for node in bpy.data.materials[mat].node_tree.nodes:
                                if node.type == "BSDF_PRINCIPLED":
                                    if len(node.inputs[21].links) > 0:
                                        bpy.data.materials[mat].blend_method = alpha_mode
                                        bpy.data.materials[mat].shadow_method = shadow_mode
                                        bpy.data.materials[mat].alpha_threshold = alpha_threshold
                                        break
                                    else:
                                        if node.inputs[21].default_value < 1.0:
                                            bpy.data.materials[mat].blend_method = alpha_mode
                                            bpy.data.materials[mat].shadow_method = shadow_mode
                                            bpy.data.materials[mat].alpha_threshold = alpha_threshold
                                            break

                        # Filter 2 - Transparent BSDF
                        elif filter_mode == "TRANSPARENTNODE":
                            for node in bpy.data.materials[mat].node_tree.nodes:
                                if node.type == "BSDF_TRANSPARENT":
                                    bpy.data.materials[mat].blend_method = alpha_mode
                                    bpy.data.materials[mat].shadow_method = shadow_mode
                                    bpy.data.materials[mat].alpha_threshold = alpha_threshold
                                    break

                        else:
                            bpy.data.materials[mat].blend_method = alpha_mode
                            bpy.data.materials[mat].shadow_method = shadow_mode
                            bpy.data.materials[mat].alpha_threshold = alpha_threshold
                            break

        return {'FINISHED'}


# End classes


def menu_func(self, context):
    self.layout.operator(PasteBakeTargetNode.bl_idname)
    self.layout.operator(CopyBakeTargetNode.bl_idname)
    self.layout.operator(DeleteBakeTargetNode.bl_idname)
    self.layout.operator(AssignUVMapNode.bl_idname)
    self.layout.operator(OverwriteUVSlotName.bl_idname)
    self.layout.operator(SetUVSlotAsActive.bl_idname)
    self.layout.operator(AssignVCToNodes.bl_idname)
    self.layout.operator(SetBlendMode.bl_idname)


# MATERIALS PANEL

class MaterialBatchToolsPanel(bpy.types.Panel):
    bl_label = 'Material Batch Tools'
    bl_idname = "MATERIAL_PT_matbatchtools"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'

    @classmethod
    def poll(cls, context):
        return (context.object is not None)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout

        # Bake Target Node UI
        box = layout.box()
        box.label(text="Bake Target Node")

        row0 = box.row()
        row1 = box.row()
        row2 = box.row()

        row0.operator("material.copy_bake_target")
        row0.operator("material.paste_bake_target")
        row1.operator("material.delete_bake_target")
        row2.prop(
            bpy.context.scene.MatBatchProperties, "BakeTargetNodeColorEnable")
        row2.prop(
            bpy.context.scene.MatBatchProperties, "BakeTargetNodeColor")

        layout.separator()

        # UV Map Node UI
        box2 = layout.box()
        box2.label(text="UV Maps")

        row3 = box2.row()
        row4 = box2.row()
        row5 = box2.row()

        row3.prop(bpy.context.scene.MatBatchProperties,
                  "UVMapNodeTarget")
        row4.prop(bpy.context.scene.MatBatchProperties,
                  "UVMapNodeExtensionFilter")
        row5.operator("material.assign_uv_map_node")

        box3 = box2.box()
        row6 = box3.row()
        row7 = box3.row()
        row8 = box3.row()

        # UV Slot UI
        row6.prop(bpy.context.scene.MatBatchProperties, "UVSlotIndex")
        row7.operator("object.overwrite_uv_slot_name")
        row8.operator("object.set_uv_slot_as_active")\

        layout.separator()

        # Vertex Colors UI
        box4 = layout.box()
        box4.label(text="Vertex Colors")
        row9 = box4.row()
        row10 = box4.row()
        row11 = box4.row()

        row9.prop(bpy.context.scene.MatBatchProperties, "VCName")
        row10.operator("material.assign_vc_to_nodes")
        row11.operator("object.rename_vertex_color")

        layout.separator()

        # Transparency UI
        box5 = layout.box()
        box5.label(text="Transparency")
        row12 = box5.row()
        row13 = box5.row()
        row14 = box5.row()
        row15 = box5.row()

        row12.prop(bpy.context.scene.MatBatchProperties, "AlphaBlendMode")
        row13.prop(bpy.context.scene.MatBatchProperties,
                   "AlphaBlendFilter")
        row14.prop(bpy.context.scene.MatBatchProperties,
                   "AlphaThreshold")
        row15.operator("material.set_blend_mode")

# End of classes


def register():
    bpy.utils.register_class(MatBatchProperties)
    bpy.types.Scene.MatBatchProperties = bpy.props.PointerProperty(
        type=MatBatchProperties)
    bpy.utils.register_class(CopyBakeTargetNode)
    bpy.utils.register_class(PasteBakeTargetNode)
    bpy.utils.register_class(DeleteBakeTargetNode)
    bpy.utils.register_class(AssignUVMapNode)
    bpy.utils.register_class(OverwriteUVSlotName)
    bpy.utils.register_class(SetUVSlotAsActive)
    bpy.utils.register_class(AssignVCToNodes)
    bpy.utils.register_class(RenameVertexColorSlot)
    bpy.utils.register_class(SetBlendMode)
    bpy.utils.register_class(MaterialBatchToolsPanel)


def unregister():
    bpy.utils.unregister_class(MatBatchProperties)
    del bpy.types.Scene.MatBatchProperties
    bpy.utils.unregister_class(PasteBakeTargetNode)
    bpy.utils.unregister_class(CopyBakeTargetNode)
    bpy.utils.unregister_class(DeleteBakeTargetNode)
    bpy.utils.unregister_class(AssignUVMapNode)
    bpy.utils.unregister_class(OverwriteUVSlotName)
    bpy.utils.unregister_class(SetUVSlotAsActive)
    bpy.utils.unregister_class(AssignVCToNodes)
    bpy.utils.unregister_class(RenameVertexColorSlot)
    bpy.utils.unregister_class(SetBlendMode)
    bpy.utils.unregister_class(MaterialBatchToolsPanel)


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()
