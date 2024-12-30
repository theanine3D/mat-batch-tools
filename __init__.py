import mathutils
import bpy

bl_info = {
    "name": "Material Batch Tools",
    "description": "Batch tools for quickly modifying, copying, and pasting nodes on all materials in selected objects",
    "author": "Theanine3D",
    "version": (1, 5, 1),
    "blender": (3, 0, 0),
    "category": "Material",
    "location": "Properties -> Material Properties",
    "support": "COMMUNITY"
}


# PROPERTY DEFINITIONS
bake_node_preset = {
    "image": "",
    "interpolation": "Linear",
    "projection": "FLAT",
    "projection_blend": 0.0,
    "extension": "REPEAT",
    "name": "Bake Target Node"
}

node_unify_settings = {
    "name": "",
    "type": "",
    "material": ""
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
    AlphaPrincipledRemove: bpy.props.BoolProperty(
        name="Remove Principled BSDF Alpha", description="If this option is enabled, and the Blend Mode is set to Opaque, the Principled BSDF's 'Alpha' input will be disconnected, and its value will be set to 1.0", default=False)
    SavedNodeName: bpy.props.StringProperty(
        name="Copied Node", description="The name of the node from which settings were copied", default="", maxlen=200)
    SavedNodeType: bpy.props.StringProperty(
        name="Copied Node Type", description="The type of the node from which settings were copied", default="", maxlen=200)
    UnifyFilterLabel: bpy.props.StringProperty(
        name="Label Filter", description="If specified, the Unify button will only affect any nodes that have this custom label. Case sensitive! Leave blank if you want to alter ALL nodes of the same type as the template node", default="", maxlen=100)
    SwitchShaderTarget: bpy.props.EnumProperty(
        name="Shader", description="The shader to switch in all materials in all selected objects to. For example, if you select Principled, any Emission nodes will be switched to Principled", items=[("EMISSION", 'Emission', 'Fullbright / shadeless shader - not affected by scene lighting', 0), ("BSDF_PRINCIPLED", 'Principled BSDF', 'Standard shader in Blender, affected by scene lighting', 1)], default=0)
    CopiedTexture: bpy.props.StringProperty(
        name="Copied Texture Name", description="The name of the active image texture copied from a selected face", default="", maxlen=200)
    Template: bpy.props.EnumProperty(
        name="Template", description="The node graph template to apply to all materials in all selected objects", items=[("ECT", 'Emissive + Color + Texture', 'Blends vertex color onto texture, if one exists', 0),
                                                                                                                         ("EC", 'Emissive + Color', 'Ignores image textures completely', 1),
                                                                                                                         ("ACCT", 'Alpha Clip + Color + Texture', 'Transparency via alpha clip, and emission', 2),
                                                                                                                         ("ACT", 'Additive + Color + Texture', 'Combines transparency and emission for an additive effect', 3),
                                                                                                                         ("AC", 'Additive + Color', 'Combines transparency and emission for an additive effect', 4),
                                                                                                                         ("PT", 'Principled + Texture', 'Principled shading, with texture', 5),
                                                                                                                         ("PC", 'Principled + Color', 'Principled shading, with vertex color', 6),
                                                                                                                         ("HDRT", 'HDR Lightmap', "Emissive but with an HDR lightmap applied for baked lighting. Your HDR's UV map must be named 'lightmap', and your HDR's filename must contain either 'light_', '.hdr' or '.exr' to be detected automatically", 7),
                                                                                                                         ("PP", 'Mirror UV', "Mirroring / ping pong effect applied to any UV Maps, on both X and Y axis", 8),
                                                                                                                         ("NO_PP", 'Unmirror UV', "Removes the mirror / ping pong effect from any UV Maps, on both X and Y axis", 9),
                                                                                                                         ], default=0)
    SkipTexture: bpy.props.StringProperty(
        name="Skip Texture", description="Any texture containing this string in its filename will NOT be assigned in any image texture when applying a material template (optional - leave blank if unneeded)", default="", maxlen=200)
    IsolateCollection: bpy.props.BoolProperty(
        name="Isolate to Collection", description="If enabled, any isolated meshes are moved to a separate collection for easier finding", default=True)
    IsolateTrait: bpy.props.EnumProperty(
        name="Trait", description="The trait to look for in materials, in order to isolate their assigned faces into a separate object", items=[("transparent", 'Transparent', "Material uses alpha transparency, via Transparent BSDF or Principled BSDF's alpha slot.", 0),
                                                                                                                         ("emissive", 'Emissive', "Material uses Emission shader or Principled BSDF's Emission slot", 1),
                                                                                                                         ], default=0)


# FUNCTION DEFINITIONS

def display_msg_box(message="", title="Info", icon='INFO'):
    ''' Open a pop-up message box to notify the user of something               '''
    ''' Example:                                                                '''
    ''' display_msg_box("This is a message", "This is a custom title", "ERROR") '''

    def draw(self, context):
        lines = message.split("\n")
        for line in lines:
            self.layout.label(text=line)
            print(line)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)

def update_alpha_settings(mat, alpha_mode, shadow_mode, alpha_threshold):
    if bpy.app.version >= (4, 2, 0):

        if alpha_mode != "CLIP":
            # Remove the Math "Greater Than" node if one exists
            for node in bpy.data.materials[mat].node_tree.nodes:
                if node.type == 'MATH' and node.operation == "GREATER_THAN":
                    bpy.data.materials[mat].node_tree.nodes.remove(node)
                    break

        if alpha_mode == "BLEND":
            alpha_mode = "BLENDED"
                
        elif alpha_mode == "CLIP":
            greaterthan_node = None
            img_tex_node = None
            principled_node = None
            mix_shader_node = None

            # Search for existing nodes first
            for node in bpy.data.materials[mat].node_tree.nodes:
                if node.type == 'MATH' and node.operation == "GREATER_THAN":
                    greaterthan_node = node
                    continue
                elif node.type == 'TEX_IMAGE' and node.image:
                    img_tex_node = node
                    continue
                elif node.type == 'MIX_SHADER':
                    mix_shader_node = node
                    continue
                elif node.type == "BSDF_PRINCIPLED":
                    principled_node = node
                    continue
            if img_tex_node is not None and (principled_node is not None or mix_shader_node is not None):
                if greaterthan_node is None:
                    greaterthan_node = bpy.data.materials[mat].node_tree.nodes.new(type='ShaderNodeMath')
                    greaterthan_node.operation = "GREATER_THAN"
                greaterthan_node.location = (img_tex_node.location.x + 100, img_tex_node.location.y - 286)
                bpy.data.materials[mat].node_tree.links.new(img_tex_node.outputs[1], greaterthan_node.inputs[0])
                if principled_node is not None:
                    bpy.data.materials[mat].node_tree.links.new(greaterthan_node.outputs[0], principled_node.inputs[4])
                elif mix_shader_node is not None:
                    bpy.data.materials[mat].node_tree.links.new(greaterthan_node.outputs[0], mix_shader_node.inputs[0])
            alpha_mode = "DITHERED"
        else:
            alpha_mode = "DITHERED"

        bpy.data.materials[mat].surface_render_method = alpha_mode
    else:
        bpy.data.materials[mat].blend_method = alpha_mode
        bpy.data.materials[mat].shadow_method = shadow_mode
        bpy.data.materials[mat].alpha_threshold = alpha_threshold

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

def check_for_selected(objectOnly=False):
    list_of_mats = set()

    # Check if any objects are selected.
    if len(bpy.context.selected_objects) > 0:

        # Check if we're only checking for selected objects, regardless if the objects have any materials
        if objectOnly == False:

            # For each selected object
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":

                    for mat in obj.material_slots.keys():

                        if mat != '':
                            list_of_mats.add(mat)

            if len(list_of_mats) > 0:
                return list(set(list_of_mats))
            else:
                display_msg_box(
                    "There are no valid materials in the selected objects", "Error", "ERROR")
                return False
    else:
        display_msg_box(
            "At least one mesh object must be selected", "Error", "ERROR")
        return False

def is_node_connected(material, node_to_check):
    ''' Checks if a specified node is actually connected (indirectly or directly) to the final Material Output'''
    
    output_node = None
    # Find the Material Output node
    for node in material.node_tree.nodes:
        if node.type == 'OUTPUT_MATERIAL':
            output_node = node
            break
    
    if not output_node:
        return False
    
    # Function to recursively check connections
    def check_connections(current_node):
        if current_node == node_to_check:
            return True
        for input_socket in current_node.inputs:
            for link in input_socket.links:
                source_node = link.from_node
                if check_connections(source_node):
                    return True
        return False
    
    # Start from the output node and check connections
    return check_connections(output_node)

def find_faces_with_material(mesh_obj, material_name):
    if material_name not in mesh_obj.data.materials:
        return []

    mat_index = mesh_obj.data.materials.find(material_name)
    faces_with_material = [poly.index for poly in mesh_obj.data.polygons if poly.material_index == mat_index]
    return faces_with_material

def separate_faces(mesh_obj, face_indices):
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.reveal()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
    bpy.ops.object.mode_set(mode='OBJECT')

    for face_index in face_indices:
        if face_index < len(mesh_obj.data.polygons):
            mesh_obj.data.polygons[face_index].select = True

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')

    for obj in bpy.context.selected_objects:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.material_slot_remove_unused()

    mesh_obj.select_set(False)
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    new_obj = bpy.context.active_object

    return new_obj


# Bake Target copy operator


class CopyBakeTargetNode(bpy.types.Operator):
    """Copy the currently active Image Texture node and set it as a preset for baking."""
    bl_idname = "material.copy_bake_target"
    bl_label = "Copy"
    bl_options = {'REGISTER'}

    def execute(self, context):

        # Check if there's actually an active object and active material
        if bpy.context.active_object != None and bpy.context.active_object.active_material != None:

            if len(bpy.context.active_object.material_slots) != 0:

                if len(bpy.context.active_object.active_material.node_tree.nodes) != 0:

                    # Check if there's an active node
                    if bpy.context.active_object.active_material.node_tree.nodes.active != None:

                        # Check if the selected, active node is actually an Image Texture.
                        if bpy.context.active_object.active_material.node_tree.nodes.active.type == "TEX_IMAGE":
                            if bpy.context.active_object.active_material.node_tree.nodes.active.image != None:
                                bake_node_preset["image"] = bpy.context.active_object.active_material.node_tree.nodes.active.image.name
                                bake_node_preset["interpolation"] = bpy.context.active_object.active_material.node_tree.nodes.active.interpolation
                                bake_node_preset["projection"] = bpy.context.active_object.active_material.node_tree.nodes.active.projection
                                bake_node_preset["projection_blend"] = bpy.context.active_object.active_material.node_tree.nodes.active.projection_blend
                                bake_node_preset["extension"] = bpy.context.active_object.active_material.node_tree.nodes.active.extension
                    else:
                        display_msg_box(
                            "There is no active Image Texture node. Click on an Image Texture node to set it as active first", "Error", "ERROR")
                else:
                    display_msg_box(
                        "The active material has no nodes. Select a valid material with at least one Image Texture node", "Error", "ERROR")
            else:
                display_msg_box(
                    "There are no valid materials in the active mesh object", "Error", "ERROR")
        else:
            display_msg_box(
                "There is no active mesh object. Click on a mesh object to set it as active first", "Error", "ERROR")

        return {'FINISHED'}


# Bake Target paste operator

class PasteBakeTargetNode(bpy.types.Operator):
    """Paste the Bake Target Node in all materials in selected objects, using the node settings previously copied with Copy button"""
    bl_idname = "material.paste_bake_target"
    bl_label = "Paste"
    bl_options = {'REGISTER'}

    def execute(self, context):

        num_processed = 0

        list_of_mats = check_for_selected()

        # Check if any objects are selected.
        if list_of_mats != False:

            # Check if an image texture has actually been copied yet
            if bake_node_preset["image"] != "":

                # For each material in selected object
                for mat in list_of_mats:

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
                    if reference_node != None:

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
                        num_processed += 1

                display_msg_box(
                    f'Created bake target in {num_processed} material(s).', 'Info', 'INFO')
            
            else:
                display_msg_box(
                    "There is no currently set Bake Target. Use the Copy button first to set one", "Error", "ERROR")

        return {'FINISHED'}


# Bake Target delete operator

class DeleteBakeTargetNode(bpy.types.Operator):
    """Delete the Bake Target Node, if present, in all materials in selected objects"""
    bl_idname = "material.delete_bake_target"
    bl_label = "Delete"
    bl_options = {'REGISTER'}

    def execute(self, context):
        num_processed = 0
        list_of_mats = check_for_selected()

        # Check if any objects are selected.
        if list_of_mats != False:

            if bake_node_preset["image"] != "":

                # For each material in selected object
                for mat in list_of_mats:

                    # Check if Bake Target Node already exists. If so, delete it.
                    for node in bpy.data.materials[mat].node_tree.nodes:
                        if "Bake Target Node" in node.name:
                            bpy.data.materials[mat].node_tree.nodes.remove(
                                node)
                            num_processed += 1
                            break

                display_msg_box(
                    f'Deleted {num_processed} bake target node(s).', 'Info', 'INFO')
            
            else:
                display_msg_box(
                    "There is no currently set Bake Target. Use the Copy button first to set one", "Error", "ERROR")
                
        return {'FINISHED'}

# Assign UV Map Node operator


class AssignUVMapNode(bpy.types.Operator):
    """Assign a UV Map node to any Image Texture that satisfies the entered Filter, in all materials in selected objects"""
    bl_idname = "material.assign_uv_map_node"
    bl_label = "Assign UV Map Node"
    bl_options = {'REGISTER'}

    def execute(self, context):
        num_processed = 0
        list_of_mats = check_for_selected()

        # Check if any objects are selected.
        if list_of_mats != False:

            # For each material in selected object
            for mat in list_of_mats:

                nodetree = bpy.data.materials[mat].node_tree
                links = bpy.data.materials[mat].node_tree.links

                # Look for Image Texture nodes
                for node in nodetree.nodes:
                    new_UV_node = None
                    reference_node = None

                    if node.type == "TEX_IMAGE" and node.image:

                        # Skip if it's a Bake Target node
                        if node.label == "Bake Target":
                            continue

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

                                # If the Image Texture has some other kind of node connected... recursively search to find the closest UV Map node
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
                                new_UV_node.outputs[0], reference_node.inputs[0])
                            num_processed += 1
                            continue
        display_msg_box(
            f'Created and assigned {num_processed} UV Map node(s).', 'Info', 'INFO')

        return {'FINISHED'}


# Overwrite UV Slot Name operator

class OverwriteUVSlotName(bpy.types.Operator):
    """Using the specified UV Map name above, this button will overwrite the name of the UV Map in the specified UV slot, in all selected objects. If UV Map slot doesn't exist, a new UV Map will be created with that name"""
    bl_idname = "object.overwrite_uv_slot_name"
    bl_label = "Overwrite UV Slot Name"
    bl_options = {'REGISTER'}

    def execute(self, context):
        num_processed = 0
        # Check if any objects are selected
        if check_for_selected(True) != False:

            # For each selected object
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":
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
                    elif uvslots[uvslot_index-1] != None:
                        uvslots[uvslot_index -
                                1].name = uvname
                    num_processed += 1
                    obj.data.update()


        display_msg_box(
            f'Renamed the UV map layer for {num_processed} object(s).', 'Info', 'INFO')

        return {'FINISHED'}


# Set UV Slot as Active opterator

class SetUVSlotAsActive(bpy.types.Operator):
    """Sets the currently selected UV Slot above as the 'active' slot in all selected objects. Does not modify the UV map name"""
    bl_idname = "object.set_uv_slot_as_active"
    bl_label = "Set UV Slot as Active"
    bl_options = {'REGISTER'}

    def execute(self, context):
        num_processed = 0
        # Check if any objects are selected
        if check_for_selected(True) != False:

            # For each selected object
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":
                    mesh = obj.data
                    uvslots = mesh.uv_layers
                    uvslot_index = int(
                        bpy.context.scene.MatBatchProperties.UVSlotIndex)
                    if len(uvslots) > 0:
                        uvslots.active = uvslots[uvslot_index - 1]
                        num_processed += 1
                    obj.data.update()


        display_msg_box(
            f'Set the active UV slot for {num_processed} object(s).', 'Info', 'INFO')
        
        return {'FINISHED'}

# Assign Vertex Color to Nodes operator


class AssignVCToNodes(bpy.types.Operator):
    """Assign the Vertex Color name above to all Color Attribute nodes, in all materials in selected objects"""
    bl_idname = "material.assign_vc_to_nodes"
    bl_label = "Assign Name to Color Nodes"
    bl_options = {'REGISTER'}

    def execute(self, context):
        num_processed = 0

        list_of_mats = check_for_selected()

        # Check if any objects are selected.
        if list_of_mats != False:

            # For each selected object
            for obj in bpy.context.selected_objects:

                if obj.type == "MESH":
                    num_processed += 1
                    
                    # For each material in selected object
                    for mat in list_of_mats:

                        for node in bpy.data.materials[mat].node_tree.nodes:

                            if node.type == "VERTEX_COLOR":
                                node.layer_name = bpy.context.scene.MatBatchProperties.VCName
                            elif node.type == "ATTRIBUTE":
                                node.attribute_name = bpy.context.scene.MatBatchProperties.VCName
                    obj.data.update()

        display_msg_box(
            f'Assigned vertex color layer in {num_processed} object(s).', 'Info', 'INFO')
        
        return {'FINISHED'}

# Rename Vertex Color Slot operator


class RenameVertexColorSlot(bpy.types.Operator):
    """Renames the first Vertex Color slot in all selected objects, using the name specified above"""
    bl_idname = "object.rename_vertex_color"
    bl_label = "Rename Vertex Color Slot 1"
    bl_options = {'REGISTER'}

    def execute(self, context):
        num_processed = 0

        # Blender 3.2 renamed "vertex colors" to "color attributes," so let's check the version beforehand
        useColorAttributes = (bpy.app.version >= (3, 2, 0))

        # Check if any objects are selected
        if check_for_selected(True) != False:

            # For each selected object
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":

                    mesh = obj.data
                    if useColorAttributes:
                        vcslots = mesh.color_attributes
                    else:
                        vcslots = mesh.vertex_colors
                    vcname = bpy.context.scene.MatBatchProperties.VCName

                    if len(vcslots) > 0:
                        vcslots[0].name = vcname
                    else:
                        if useColorAttributes:
                            vcslots.new(name=vcname, type="FLOAT_COLOR",
                                        domain="POINT")
                            # vcslots.new(name=vcname, type="BYTE_COLOR",
                            #             domain="CORNER")
                        else:
                            vcslots.new(name=vcname)
                        
                    num_processed += 1
                    obj.data.update()

        display_msg_box(
            f'Renamed {num_processed} vertex color slot(s).', 'Info', 'INFO')
        return {'FINISHED'}

# Convert Vertex Color operator

class ConvertVertexColor(bpy.types.Operator):
    """Converts the data type of the first Color Attribute slot in all selected objects, between 'Face Corner Byte Color' and 'Vertex Color'"""
    bl_idname = "object.convert_vertex_color"
    bl_label = "Convert Vertex Color Slot 1"
    bl_options = {'REGISTER'}

    def execute(self, context):

        # Blender 3.2 renamed "vertex colors" to "color attributes," so let's check the version beforehand
        useColorAttributes = (bpy.app.version >= (3, 2, 0))

        if not useColorAttributes:
            display_msg_box(
                f'This feature is only available in Blender 3.2 or higher.', 'Error', 'ERROR')
            return {'FINISHED'}

        num_processed = 0

        # Check if any objects are selected
        if check_for_selected(True) != False:

            # For each selected object
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":

                    mesh = obj.data
                    vcslots = mesh.color_attributes
                    vcname = bpy.context.scene.MatBatchProperties.VCName

                    if len(vcslots) == 1:
                        if vcslots[0].data_type == "FLOAT_COLOR":
                            vcslots.remove(vcslots[0])
                            vcslots.new(name=vcname, type="BYTE_COLOR",
                                        domain="CORNER")
                        elif vcslots[0].data_type == "BYTE_COLOR":
                            vcslots.remove(vcslots[0])
                            vcslots.new(name=vcname, type="FLOAT_COLOR",
                                        domain="POINT")
                        num_processed += 1
                    obj.data.update()

        display_msg_box(
            f'Converted {num_processed} color attribute slot(s).', 'Info', 'INFO')
        return {'FINISHED'}


# Set Blend Mode operator

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
        principled_alpha_slot = 21 if bpy.app.version < (4, 0, 0) else 4

        if alpha_mode == "BLEND":
            shadow_mode = "CLIP"

        list_of_mats = check_for_selected()

        # Check if any objects are selected.
        if list_of_mats != False:

            # For each selected object
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":

                    # For each material in selected object
                    for mat in list_of_mats:

                        principled_nodes = []
                        for node in bpy.data.materials[mat].node_tree.nodes:
                            if node.type == "BSDF_PRINCIPLED":
                                principled_nodes.append(node)

                        # If user also wants to remove any alpha from the Principled node itself too
                        if bpy.context.scene.MatBatchProperties.AlphaPrincipledRemove == True and alpha_mode == "OPAQUE":
                            for node in principled_nodes:
                                if len(node.inputs[principled_alpha_slot].links) > 0:
                                    bpy.data.materials[mat].node_tree.links.remove(
                                        node.inputs[principled_alpha_slot].links[0])
                                node.inputs[principled_alpha_slot].default_value = 1.0

                        # Filter 1 - Principled BSDF with Alpha
                        if filter_mode == "PRINCIPLEDNODE":
                            for node in bpy.data.materials[mat].node_tree.nodes:
                                if node.type == "BSDF_PRINCIPLED":
                                    if len(node.inputs[principled_alpha_slot].links) > 0:
                                        update_alpha_settings(mat, alpha_mode, shadow_mode, alpha_threshold)
                                        break
                                    else:
                                        if node.inputs[principled_alpha_slot].default_value < 1.0:
                                            update_alpha_settings(mat, alpha_mode, shadow_mode, alpha_threshold)
                                            break

                        # Filter 2 - Transparent BSDF
                        elif filter_mode == "TRANSPARENTNODE":
                            for node in bpy.data.materials[mat].node_tree.nodes:
                                    update_alpha_settings(mat, alpha_mode, shadow_mode, alpha_threshold)
                                    break

                        else:
                            update_alpha_settings(mat, alpha_mode, shadow_mode, alpha_threshold)
                            continue
                    obj.data.update()

        return {'FINISHED'}


# Copy Node Settings operator

class SetAsTemplateNode(bpy.types.Operator):
    """Stores the currently active, selected node as a template"""
    bl_idname = "material.set_as_template_node"
    bl_label = "Set as Template Node"
    bl_options = {'REGISTER'}

    def execute(self, context):

        global node_unify_settings

        node_unify_settings = {
            "name": "",
            "type": "",
            "material": ""
        }

        # Check if there's an active object
        if bpy.context.active_object != None:

            # Check if there's an active node
            if bpy.context.active_object.active_material.node_tree.nodes.active != None:

                active_node = bpy.context.active_object.active_material.node_tree.nodes.active

                node_unify_settings["name"] = active_node.name
                node_unify_settings["type"] = active_node.type
                node_unify_settings["material"] = bpy.context.active_object.active_material.name
                bpy.context.scene.MatBatchProperties.SavedNodeName = active_node.name
                bpy.context.scene.MatBatchProperties.SavedNodeType = active_node.bl_label
            else:
                display_msg_box(
                    "There is no active node. Click on a node to set one as active", "Error", "ERROR")
        else:
            display_msg_box(
                "There is no active mesh object. Click on a mesh object to set one as active", "Error", "ERROR")

        return {'FINISHED'}


# Unify Node Settings operator

class UnifyNodeSettings(bpy.types.Operator):
    """Searches for all nodes of the same type, in all materials on selected objects, and copies the template node's settings into those other nodes' settings. The original template node is not modified and must still exist"""
    bl_idname = "material.unify_node_settings"
    bl_label = "Unify Node Settings"
    bl_options = {'REGISTER'}

    def execute(self, context):
        num_processed = 0
        node_type = node_unify_settings["type"]

        # Check if template node's material still exists:
        if bpy.data.materials.get(node_unify_settings["material"]) != None:

            # Check if template node still exists:
            if bpy.data.materials[node_unify_settings["material"]].node_tree.nodes.get(node_unify_settings["name"]) != None:

                template_node = bpy.data.materials[node_unify_settings["material"]
                                                   ].node_tree.nodes[node_unify_settings["name"]]

                list_of_mats = check_for_selected()

                # Check if any objects are selected.
                if list_of_mats != False:

                    # Check if there are any previously copied node settings
                    if node_unify_settings["name"] != "":

                        # For each selected object
                        for obj in bpy.context.selected_objects:
                            if obj.type == "MESH":
                                num_processed += 1

                                # For each material in selected object
                                for mat in list_of_mats:

                                    valid_nodes = []

                                    for node in bpy.data.materials[mat].node_tree.nodes:

                                        # Check if node is of the saved type
                                        if node.type == node_type:

                                            # Check if a Label Filter was specified
                                            if bpy.context.scene.MatBatchProperties.UnifyFilterLabel != "":
                                                if node.label == bpy.context.scene.MatBatchProperties.UnifyFilterLabel:
                                                    valid_nodes.append(node)
                                                else:
                                                    continue

                                            else:
                                                valid_nodes.append(node)
                                                
                                    for node in valid_nodes:

                                        # Copy and paste inputs from template node
                                        input_counter = 0

                                        for i in node.inputs:

                                            if hasattr(i, "default_value") and hasattr(template_node.inputs[input_counter], "default_value"):

                                                i.default_value = template_node.inputs[
                                                    input_counter].default_value
                                                input_counter += 1

                                        # Copy and paste properties from template node, but exclude the properties contained in a "do not use" list
                                        property_list = list(
                                            template_node.bl_rna.properties.keys())
                                        new_property_list = list()

                                        do_not_use = ['rna_type', 'type', 'location', 'width', 'width_hidden', 'height', 'dimensions', 'name', 'label', 'inputs', 'outputs', 'internal_links', 'parent', 'use_custom_color', 'color', 'select', 'show_options',
                                                      'show_preview', 'hide', 'mute', 'show_texture', 'bl_idname', 'bl_label', 'bl_description', 'bl_icon', 'bl_static_type', 'bl_width_default', 'bl_width_min', 'bl_width_max', 'bl_height_default', 'bl_height_min', 'bl_height_max']

                                        for prop in property_list:
                                            if prop not in do_not_use:
                                                if node.is_property_readonly(prop) == False:
                                                    new_property_list.append(
                                                        prop)

                                        for prop in new_property_list:
                                            setattr(
                                                node, prop, eval(f"template_node.{prop}"))
                    else:
                        display_msg_box(
                            "You haven't set a a template yet. Use the Set as Template button to set one.", "Error", "ERROR")
            else:
                display_msg_box(
                    "The template node no longer exists. Use the Set as Template button set a new one", "Error", "ERROR")
        else:
            display_msg_box(
                "The template node's parent material no longer exists. Use the Set as Template button set a new one", "Error", "ERROR")
        
        display_msg_box(
            f'Applied unified node settings in {num_processed} object(s).', 'Info', 'INFO')
        return {'FINISHED'}

# Shader Switch operator


class SwitchShader(bpy.types.Operator):
    """Finds all Principled BSDF or Emission shader nodes, in all materials in all selected objects, and switches them to the shader selected above"""
    bl_idname = "material.switch_shader"
    bl_label = "Switch Shader"
    bl_options = {'REGISTER'}

    def execute(self, context):

        num_processed = 0
        list_of_mats = check_for_selected()

        # Check if any objects are selected.
        if list_of_mats != False:

            old_shader_type = None
            target_shader_type = bpy.context.scene.MatBatchProperties.SwitchShaderTarget

            if target_shader_type == "EMISSION":  # If user wants to switch to Emission
                old_shader_type = "BSDF_PRINCIPLED"
            else:
                old_shader_type = "EMISSION"

            # For each selected object
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":

                    # For each material in selected object
                    for mat in list_of_mats:

                        # Check if there's actually a material in the material slot
                        if mat != '':
                            material = bpy.data.materials[mat]

                            # Find the other shader
                            old_shaders = []
                            for node in bpy.data.materials[mat].node_tree.nodes:
                                if node.type == old_shader_type:
                                    old_shaders.append(node)
                                    break

                            # If the old shader wasn't found, skip this material and continue to the next material
                            if len(old_shaders) == 0:
                                continue

                            # If opposite shader was found:
                            else:

                                for old_shader in old_shaders:

                                    new_shader = None
                                    input_node_socket = None
                                    output_node_socket = None

                                    if len(old_shader.inputs[0].links) > 0:
                                        input_node_socket = old_shader.inputs[0].links[0].from_socket
                                    if len(old_shader.outputs[0].links) > 0:
                                        output_node_socket = old_shader.outputs[0].links[0].to_socket

                                    # Create new shader
                                    if target_shader_type == "BSDF_PRINCIPLED":
                                        new_shader = bpy.data.materials[mat].node_tree.nodes.new(
                                            "ShaderNodeBsdfPrincipled")

                                    if target_shader_type == "EMISSION":
                                        new_shader = bpy.data.materials[mat].node_tree.nodes.new(
                                            "ShaderNodeEmission")

                                    # Place the new shader in the old shader's location
                                    new_shader.location = old_shader.location
                                    if len(old_shader.inputs[0].links) > 0:
                                        material.node_tree.links.new(
                                            new_shader.inputs[0], input_node_socket)
                                    if len(old_shader.outputs[0].links) > 0:
                                        material.node_tree.links.new(
                                            output_node_socket, new_shader.outputs[0])
                                    material.node_tree.nodes.remove(old_shader)
                                    num_processed += 1

        display_msg_box(
            f'Switched shader in {num_processed} material(s).', 'Info', 'INFO')

        return {'FINISHED'}

# Apply Material Template operator

class ApplyMatTemplate(bpy.types.Operator):
    """Applies the selected material template, to all materials in all selected objects, while attempting to retain the albedo image texture if one exists"""
    bl_idname = "material.apply_mat_template"
    bl_label = "Apply Material Template"
    bl_options = {'REGISTER'}

    def execute(self, context):

        num_processed = 0
        list_of_mats = check_for_selected()
        useColorAttributes = bpy.app.version >= (3, 2, 0)
        mix_node_type = "ShaderNodeMixRGB" if bpy.app.version < (3, 4, 0) else "ShaderNodeMix"
        principled_alpha_slot = 21 if bpy.app.version < (4, 0, 0) else 4

        # Check if any objects are selected.
        if list_of_mats != False:

            target_template = bpy.context.scene.MatBatchProperties.Template
            skip_texture = bpy.context.scene.MatBatchProperties.SkipTexture
        
            # For each selected object
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":

                    # For each material in selected object
                    for mat in list_of_mats:

                        # Check if there's actually a material in the material slot
                        if mat != '':

                            material = bpy.data.materials[mat]
                            material.use_nodes = True

                            if material and material.use_nodes:

                                match target_template:

                                    case "ECT":

                                        if bpy.app.version >= (4, 2, 0):
                                            material.surface_render_method = 'DITHERED'
                                        else:
                                            material.blend_method = 'OPAQUE'

                                        # Store the image of the existing image texture node (if any)
                                        stored_image = None
                                        for node in material.node_tree.nodes:
                                            if node.type == 'TEX_IMAGE' and node.image:
                                                stored_image = node.image
                                                break

                                        # Clear existing nodes
                                        material.node_tree.nodes.clear()
                                        if stored_image != None:
                                            if skip_texture != "":
                                                if skip_texture in stored_image.filepath:
                                                    stored_image = None

                                        # Create necessary nodes
                                        uv_map_node = None
                                        img_tex_node = None
                                        mix_color_node = None
                                        if stored_image != None:
                                            uv_map_node = material.node_tree.nodes.new(type='ShaderNodeUVMap')
                                            img_texture_node = material.node_tree.nodes.new(type='ShaderNodeTexImage')
                                            mix_color_node = material.node_tree.nodes.new(type=mix_node_type)
                                            if "MixRGB" not in mix_node_type:
                                                mix_color_node.data_type = 'RGBA'
                                            mix_color_node.blend_type = 'MULTIPLY'
                                            mix_color_node.inputs[0].default_value = 1.0  # Set the factor to 1.0
                                            img_texture_node.image = stored_image
                                            if len(obj.data.uv_layers) > 0:
                                                uv_map_node.uv_map = obj.data.uv_layers[0].name
                                        color_attr_node = material.node_tree.nodes.new(type='ShaderNodeVertexColor')
                                        emission_node = material.node_tree.nodes.new(type='ShaderNodeEmission')
                                        material_output_node = material.node_tree.nodes.new(type='ShaderNodeOutputMaterial')

                                        # Arrange nodes for clarity
                                        if stored_image != None:
                                            img_texture_node.location = (-500, 0)
                                            mix_color_node.location = (-200, 100)
                                            uv_map_node.location = (-700, 0)
                                        color_attr_node.location = (-400, 150)
                                        emission_node.location = (0, 100)
                                        material_output_node.location = (200, 100)

                                        # Add correct Vertex Color name
                                        if useColorAttributes:
                                            if len(obj.data.color_attributes) > 0:
                                                color_attr_node.layer_name = obj.data.color_attributes[0].name
                                        else:
                                            if len(obj.data.vertex_colors) > 0:
                                                color_attr_node.layer_name = obj.data.vertex_colors[0].name

                                        # Link nodes
                                        links = material.node_tree.links
                                        if stored_image != None:
                                            if "MixRGB" not in mix_node_type:
                                                links.new(img_texture_node.outputs[0], mix_color_node.inputs[7])
                                                links.new(color_attr_node.outputs[0], mix_color_node.inputs[6])
                                                links.new(mix_color_node.outputs[2], emission_node.inputs[0])
                                            else:
                                                links.new(img_texture_node.outputs[0], mix_color_node.inputs[2])
                                                links.new(color_attr_node.outputs[0], mix_color_node.inputs[1])
                                                links.new(mix_color_node.outputs[0], emission_node.inputs[0])
                                            links.new(emission_node.outputs[0], material_output_node.inputs[0])
                                            links.new(uv_map_node.outputs[0], img_texture_node.inputs[0])
                                        else:
                                            links.new(color_attr_node.outputs[0], emission_node.inputs[0])
                                            links.new(emission_node.outputs[0], material_output_node.inputs[0])

                                    case "EC":

                                        if bpy.app.version >= (4, 2, 0):
                                            material.surface_render_method = 'DITHERED'
                                        else:
                                            material.blend_method = 'OPAQUE'

                                        # Clear existing nodes
                                        material.node_tree.nodes.clear()

                                        # Create necessary nodes
                                        color_attr_node = material.node_tree.nodes.new(type='ShaderNodeVertexColor')
                                        emission_node = material.node_tree.nodes.new(type='ShaderNodeEmission')
                                        material_output_node = material.node_tree.nodes.new(type='ShaderNodeOutputMaterial')

                                        # Arrange nodes for clarity
                                        color_attr_node.location = (-200, 100)
                                        emission_node.location = (0, 100)
                                        material_output_node.location = (200, 100)

                                        # Add correct Vertex Color name
                                        if useColorAttributes:
                                            if len(obj.data.color_attributes) > 0:
                                                color_attr_node.layer_name = obj.data.color_attributes[0].name
                                        else:
                                            if len(obj.data.vertex_colors) > 0:
                                                color_attr_node.layer_name = obj.data.vertex_colors[0].name

                                        # Link nodes
                                        links = material.node_tree.links
                                        links.new(color_attr_node.outputs[0], emission_node.inputs[0])
                                        links.new(emission_node.outputs[0], material_output_node.inputs[0])

                                    case "ACCT":

                                        if bpy.app.version >= (4, 2, 0):
                                            material.surface_render_method = 'DITHERED'
                                        else:
                                            material.blend_method = 'CLIP'
                                        
                                        # Store the image of the existing image texture node (if any)
                                        stored_image = None
                                        for node in material.node_tree.nodes:
                                            if node.type == 'TEX_IMAGE' and node.image:
                                                stored_image = node.image
                                                break

                                        # Clear existing nodes
                                        material.node_tree.nodes.clear()
                                        if stored_image != None:
                                            if skip_texture != "":
                                                if skip_texture in stored_image.filepath:
                                                    stored_image = None

                                        # Create necessary nodes
                                        if stored_image is not None:
                                            uv_map_node = material.node_tree.nodes.new(type='ShaderNodeUVMap')
                                            img_texture_node = material.node_tree.nodes.new(type='ShaderNodeTexImage')
                                            mix_color_node = material.node_tree.nodes.new(type=mix_node_type)
                                            if "MixRGB" not in mix_node_type:
                                                mix_color_node.data_type = 'RGBA'
                                            mix_color_node.blend_type = 'MULTIPLY'
                                            mix_color_node.inputs[0].default_value = 1.0  # Set the factor to 1.0
                                            img_texture_node.image = stored_image
                                            if len(obj.data.uv_layers) > 0:
                                                uv_map_node.uv_map = obj.data.uv_layers[0].name

                                        color_attr_node = material.node_tree.nodes.new(type='ShaderNodeVertexColor')
                                        emission_node = material.node_tree.nodes.new(type='ShaderNodeEmission')
                                        material_output_node = material.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
                                        mix_shader_node = material.node_tree.nodes.new(type='ShaderNodeMixShader')
                                        transparent_node = material.node_tree.nodes.new(type='ShaderNodeBsdfTransparent')

                                        material.alpha_threshold = 0.5

                                        # Add correct Vertex Color name
                                        if useColorAttributes:
                                            if len(obj.data.color_attributes) > 0:
                                                color_attr_node.layer_name = obj.data.color_attributes[0].name
                                        else:
                                            if len(obj.data.vertex_colors) > 0:
                                                color_attr_node.layer_name = obj.data.vertex_colors[0].name

                                        # Arrange nodes for clarity
                                        if stored_image is not None:
                                            uv_map_node.location = (-700, 0)
                                            img_texture_node.location = (-500, 0)
                                            mix_color_node.location = (-200, 100)

                                        color_attr_node.location = (-400, 150)
                                        emission_node.location = (0, 100)
                                        mix_shader_node.location = (200, 100)
                                        transparent_node.location = (0, -100)
                                        material_output_node.location = (400, 100)

                                        # Link nodes
                                        links = material.node_tree.links
                                        if stored_image is not None:
                                            links.new(uv_map_node.outputs[0], img_texture_node.inputs[0])
                                            links.new(img_texture_node.outputs[0], mix_color_node.inputs[2])

                                            if "MixRGB" not in mix_node_type:
                                                links.new(img_texture_node.outputs[0], mix_color_node.inputs[7])
                                                links.new(color_attr_node.outputs[0], mix_color_node.inputs[6])
                                                links.new(mix_color_node.outputs[2], emission_node.inputs[0])
                                            else:
                                                links.new(img_texture_node.outputs[0], mix_color_node.inputs[2])
                                                links.new(color_attr_node.outputs[0], mix_color_node.inputs[1])
                                                links.new(mix_color_node.outputs[0], emission_node.inputs[0])
                                        else:
                                            links.new(color_attr_node.outputs[0], emission_node.inputs[0])
                                            links.new(emission_node.outputs[0], material_output_node.inputs[0])

                                        # Mix Shader links
                                        links.new(emission_node.outputs[0], mix_shader_node.inputs[2])
                                        links.new(transparent_node.outputs[0], mix_shader_node.inputs[1])
                                        links.new(img_texture_node.outputs[1], mix_shader_node.inputs[0])
                                        links.new(mix_shader_node.outputs[0], material_output_node.inputs[0])

                                        # Blender 4.2 got rid of the alpha clip setting, so we use the Math node instead
                                        if bpy.app.version >= (4, 2, 0):
                                            material.surface_render_method = 'DITHERED'
                                            greaterthan_node = material.node_tree.nodes.new(type='ShaderNodeMath')
                                            greaterthan_node.operation = 'GREATER_THAN'
                                            greaterthan_node.location = (-200,-140)
                                            links.new(img_texture_node.outputs[1], greaterthan_node.inputs[0])
                                            links.new(greaterthan_node.outputs[0], mix_shader_node.inputs[0])
                                        else:
                                            material.blend_method = "CLIP"


                                    case "ACT":

                                        material.blend_method = "BLEND"
                                        
                                        # Store the image of the existing image texture node (if any)
                                        stored_image = None
                                        for node in material.node_tree.nodes:
                                            if node.type == 'TEX_IMAGE' and node.image:
                                                stored_image = node.image
                                                break

                                        # Clear existing nodes
                                        material.node_tree.nodes.clear()
                                        if stored_image != None:
                                            if skip_texture != "":
                                                if skip_texture in stored_image.filepath:
                                                    stored_image = None

                                        # Create necessary nodes
                                        if stored_image is not None:
                                            uv_map_node = material.node_tree.nodes.new(type='ShaderNodeUVMap')
                                            img_texture_node = material.node_tree.nodes.new(type='ShaderNodeTexImage')
                                            mix_color_node = material.node_tree.nodes.new(type=mix_node_type)
                                            if "MixRGB" not in mix_node_type:
                                                mix_color_node.data_type = 'RGBA'
                                            mix_color_node.blend_type = 'MULTIPLY'
                                            mix_color_node.inputs[0].default_value = 1.0  # Set the factor to 1.0
                                            img_texture_node.image = stored_image
                                            if len(obj.data.uv_layers) > 0:
                                                uv_map_node.uv_map = obj.data.uv_layers[0].name

                                        color_attr_node = material.node_tree.nodes.new(type='ShaderNodeVertexColor')
                                        emission_node = material.node_tree.nodes.new(type='ShaderNodeEmission')
                                        material_output_node = material.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
                                        add_shader_node = material.node_tree.nodes.new(type='ShaderNodeAddShader')
                                        transparent_node = material.node_tree.nodes.new(type='ShaderNodeBsdfTransparent')

                                        # Add correct Vertex Color name
                                        if useColorAttributes:
                                            if len(obj.data.color_attributes) > 0:
                                                color_attr_node.layer_name = obj.data.color_attributes[0].name
                                        else:
                                            if len(obj.data.vertex_colors) > 0:
                                                color_attr_node.layer_name = obj.data.vertex_colors[0].name

                                        # Arrange nodes for clarity
                                        if stored_image is not None:
                                            uv_map_node.location = (-700, 0)
                                            img_texture_node.location = (-500, 0)
                                            mix_color_node.location = (-200, 100)

                                        color_attr_node.location = (-400, 150)
                                        emission_node.location = (0, 100)
                                        add_shader_node.location = (200, 100)
                                        transparent_node.location = (0, -100)
                                        material_output_node.location = (400, 100)

                                        # Link nodes
                                        links = material.node_tree.links
                                        if stored_image is not None:
                                            links.new(uv_map_node.outputs[0], img_texture_node.inputs[0])
                                            links.new(img_texture_node.outputs[0], mix_color_node.inputs[2])

                                            if "MixRGB" not in mix_node_type:
                                                links.new(img_texture_node.outputs[0], mix_color_node.inputs[7])
                                                links.new(color_attr_node.outputs[0], mix_color_node.inputs[6])
                                                links.new(mix_color_node.outputs[2], emission_node.inputs[0])
                                            else:
                                                links.new(img_texture_node.outputs[0], mix_color_node.inputs[2])
                                                links.new(color_attr_node.outputs[0], mix_color_node.inputs[1])
                                                links.new(mix_color_node.outputs[0], emission_node.inputs[0])
                                        else:
                                            links.new(color_attr_node.outputs[0], emission_node.inputs[0])
                                            links.new(emission_node.outputs[0], material_output_node.inputs[0])

                                        # Additive links
                                        links.new(emission_node.outputs[0], add_shader_node.inputs[0])
                                        links.new(transparent_node.outputs[0], add_shader_node.inputs[1])
                                        links.new(add_shader_node.outputs[0], material_output_node.inputs[0])

                                    case "AC":

                                        material.blend_method = "BLEND"

                                        # Clear existing nodes
                                        material.node_tree.nodes.clear()

                                        # Create necessary nodes
                                        color_attr_node = material.node_tree.nodes.new(type='ShaderNodeVertexColor')
                                        emission_node = material.node_tree.nodes.new(type='ShaderNodeEmission')
                                        material_output_node = material.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
                                        add_shader_node = material.node_tree.nodes.new(type='ShaderNodeAddShader')
                                        transparent_node = material.node_tree.nodes.new(type='ShaderNodeBsdfTransparent')

                                        # Add correct Vertex Color name
                                        if useColorAttributes:
                                            if len(obj.data.color_attributes) > 0:
                                                color_attr_node.layer_name = obj.data.color_attributes[0].name
                                        else:
                                            if len(obj.data.vertex_colors) > 0:
                                                color_attr_node.layer_name = obj.data.vertex_colors[0].name

                                        # Arrange nodes for clarity
                                        color_attr_node.location = (-200, 100)
                                        emission_node.location = (0, 100)
                                        add_shader_node.location = (200, 100)
                                        transparent_node.location = (0, -100)
                                        material_output_node.location = (400, 100)

                                        # Link nodes
                                        links = material.node_tree.links
                                        links.new(color_attr_node.outputs[0], emission_node.inputs[0])
                                        links.new(emission_node.outputs[0], material_output_node.inputs[0])

                                        # Additive links
                                        links.new(emission_node.outputs[0], add_shader_node.inputs[0])
                                        links.new(transparent_node.outputs[0], add_shader_node.inputs[1])
                                        links.new(add_shader_node.outputs[0], material_output_node.inputs[0])

                                    case "PT":

                                        if bpy.app.version >= (4, 2, 0):
                                            material.surface_render_method = 'DITHERED'
                                        else:
                                            material.blend_method = 'OPAQUE'
                                        uses_transparency = False
                                        has_alpha_channel = True

                                        # Store the image of the existing image texture node (if any)
                                        stored_image = None
                                        for node in material.node_tree.nodes:
                                            if node.type == 'TEX_IMAGE' and node.image:
                                                stored_image = node.image

                                                # Check if the found texture (if any) was being used for transparency previously
                                                for output in node.outputs:
                                                    if output.links:
                                                        for link in output.links:
                                                            if (link.to_node.type == "BSDF_PRINCIPLED" and link.to_socket.identifier == "Alpha") or (link.to_node.type == "MIX_SHADER" and link.to_socket.identifier == "Fac") or (link.to_node.type == "MATH" and link.to_node.operation == "GREATER_THAN"):
                                                                uses_transparency = True
                                                                has_alpha_channel = True if output.identifier == "Alpha" else False
                                                                break
                                                break

                                        nodes = material.node_tree.nodes
                                        links = material.node_tree.links

                                        nodes.clear()

                                        # Create nodes: UV Map, Image Texture, Principled BSDF, Material Output
                                        if stored_image != None:
                                            uv_map_node = nodes.new(type='ShaderNodeUVMap')
                                            img_tex_node = nodes.new(type='ShaderNodeTexImage')
                                            if len(obj.data.uv_layers) > 0:
                                                uv_map_node.uv_map = obj.data.uv_layers[0].name
                                            img_tex_node.image = stored_image
                                        principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')
                                        material_output_node = nodes.new(type='ShaderNodeOutputMaterial')

                                        # Set positions for the nodes
                                        if stored_image != None:
                                            uv_map_node.location = (-700, 0)
                                            img_tex_node.location = (-500, 0)
                                        principled_node.location = (-200, 0)
                                        material_output_node.location = (100, 0)

                                        # Create links between nodes
                                        if stored_image != None:
                                            links.new(uv_map_node.outputs[0], img_tex_node.inputs[0])
                                            links.new(img_tex_node.outputs[0], principled_node.inputs[0])
                                        links.new(principled_node.outputs[0], material_output_node.inputs[0])

                                        if uses_transparency:
                                            # Blender 4.0 moved the # of the Principled BSDF's Alpha input
                                            links.new(img_tex_node.outputs[1 if has_alpha_channel else 0],principled_node.inputs[principled_alpha_slot])

                                            if bpy.app.version >= (4, 2, 0):
                                                material.surface_render_method = 'DITHERED'
                                                greaterthan_node = material.node_tree.nodes.new(type='ShaderNodeMath')
                                                greaterthan_node.operation = "GREATER_THAN"
                                                greaterthan_node.location = (-377, -83)
                                                img_tex_node.location = (-655, 0)
                                                uv_map_node.location = (-854, 0)
                                                links.new(img_tex_node.outputs[1], greaterthan_node.inputs[0])
                                                links.new(greaterthan_node.outputs[0], principled_node.inputs[4])
                                            else:
                                                material.blend_method = "CLIP"
                                                material.alpha_threshold = 0.5

                                    case "PC":
                                        if bpy.app.version >= (4, 2, 0):
                                            material.surface_render_method = 'DITHERED'
                                        else:
                                            material.blend_method = 'OPAQUE'

                                        # Store the image of the existing image texture node (if any)

                                        nodes = material.node_tree.nodes
                                        links = material.node_tree.links

                                        nodes.clear()

                                        # Create nodes: Color Attribute, Principled BSDF, Material Output
                                        color_attr_node = nodes.new(type='ShaderNodeVertexColor')
                                        principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')
                                        material_output_node = nodes.new(type='ShaderNodeOutputMaterial')

                                        # Add correct Vertex Color name
                                        if useColorAttributes:
                                            if len(obj.data.color_attributes) > 0:
                                                color_attr_node.layer_name = obj.data.color_attributes[0].name
                                        else:
                                            if len(obj.data.vertex_colors) > 0:
                                                color_attr_node.layer_name = obj.data.vertex_colors[0].name

                                        # Set positions for the nodes
                                        color_attr_node.location = (-400, 0)
                                        principled_node.location = (-200, 0)
                                        material_output_node.location = (100, 0)

                                        # Create links between nodes
                                        links.new(color_attr_node.outputs[0], principled_node.inputs[0])
                                        links.new(principled_node.outputs[0], material_output_node.inputs[0])

                                    case "HDRT":

                                        if bpy.app.version >= (4, 2, 0):
                                            material.surface_render_method = 'BLENDED'
                                        else:
                                            material.blend_method = 'OPAQUE'
                                        
                                        # Store the image of the existing image texture node (if any)
                                        stored_image = None
                                        stored_hdr_image = None

                                        for node in material.node_tree.nodes:
                                            if node.type == 'TEX_IMAGE' and node.image:
                                                # An extra check to make sure we're not using the HDR texture as the albedo
                                                if not ('OPEN_EXR' in node.image.file_format or 'HDR' in node.image.file_format or 'lightmap' in node.image.name_full):
                                                    if is_node_connected(material, node):
                                                        stored_image = node.image
                                                        break

                                        for node in material.node_tree.nodes:
                                            if node.type == 'TEX_IMAGE' and node.image:
                                                # Find the HDR texture in the material and store it, if one was already present 
                                                if 'OPEN_EXR' in node.image.file_format or 'HDR' in node.image.file_format or 'lightmap' in node.image.name_full:
                                                    stored_hdr_image = node.image
                                                    break

                                        # Clear existing nodes and check if the designated "skipped texture" was stored
                                        material.node_tree.nodes.clear()
                                        if stored_image != None:
                                            if skip_texture != "":
                                                if skip_texture in stored_image.filepath:
                                                    stored_image = None

                                        # Create necessary nodes
                                        uv_map_node = None
                                        uv_hdr_map_node = None
                                        img_tex_node = None
                                        mix_color_node = None
                                        hdr_tex_node = material.node_tree.nodes.new(type='ShaderNodeTexImage')
                                        uv_hdr_map_node = material.node_tree.nodes.new(type='ShaderNodeUVMap')
                                        if stored_image != None:
                                            uv_map_node = material.node_tree.nodes.new(type='ShaderNodeUVMap')
                                            img_tex_node = material.node_tree.nodes.new(type='ShaderNodeTexImage')
                                            mix_color_node = material.node_tree.nodes.new(type=mix_node_type)
                                            if "MixRGB" not in mix_node_type:
                                                mix_color_node.data_type = 'RGBA'
                                            mix_color_node.blend_type = 'MULTIPLY'
                                            if "MIX_RGB" in mix_color_node.type:
                                                mix_color_node.use_clamp = False
                                            else:
                                                mix_color_node.clamp_factor = False
                                                mix_color_node.clamp_result = False
                                            mix_color_node.inputs[0].default_value = 1.0  # Set the factor to 1.0
                                            img_tex_node.image = stored_image
                                            if len(obj.data.uv_layers) > 0:
                                                uv_map_node.uv_map = obj.data.uv_layers[0].name
                                        emission_node = material.node_tree.nodes.new(type='ShaderNodeEmission')
                                        material_output_node = material.node_tree.nodes.new(type='ShaderNodeOutputMaterial')

                                        # Arrange nodes for clarity
                                        if stored_image != None:
                                            img_tex_node.location = (-500, 0)
                                            mix_color_node.location = (-200, 100)
                                            uv_map_node.location = (-700, 0)
                                        hdr_tex_node.location = (-500, 350)
                                        uv_hdr_map_node.location = (hdr_tex_node.location.x - 200, hdr_tex_node.location.y)
                                        emission_node.location = (0, 100)
                                        material_output_node.location = (200, 100)

                                        # Look for an HDR texture already stored in this Blender file, if one wasn't found earlier
                                        if stored_hdr_image != None:
                                            hdr_tex_node.image = stored_hdr_image
                                        else:
                                            for searched_img in bpy.data.images:
                                                if 'OPEN_EXR' in searched_img.file_format or 'HDR' in searched_img.file_format or 'lightmap' in searched_img.name_full:
                                                    hdr_tex_node.image = searched_img
                                        hdr_tex_node.label = "HDR Lightmap"
                                        uv_hdr_map_node.uv_map = "lightmap"

                                        # Link nodes
                                        links = material.node_tree.links

                                        print(f"\nStored image is: {stored_image}")
                                        if stored_image != None:
                                            if "MixRGB" not in mix_node_type:
                                                links.new(img_tex_node.outputs[0], mix_color_node.inputs[7])
                                                links.new(hdr_tex_node.outputs[0], mix_color_node.inputs[6])
                                                links.new(mix_color_node.outputs[2], emission_node.inputs[0])
                                            else:
                                                links.new(img_tex_node.outputs[0], mix_color_node.inputs[2])
                                                links.new(hdr_tex_node.outputs[0], mix_color_node.inputs[1])
                                                links.new(mix_color_node.outputs[0], emission_node.inputs[0])
                                            links.new(emission_node.outputs[0], material_output_node.inputs[0])
                                            links.new(uv_map_node.outputs[0], img_tex_node.inputs[0])
                                        else:
                                            links.new(hdr_tex_node.outputs[0], emission_node.inputs[0])
                                            links.new(emission_node.outputs[0], material_output_node.inputs[0])
                                        links.new(uv_hdr_map_node.outputs[0], hdr_tex_node.inputs[0])

                                    case "PP":
                                        node_tree = material.node_tree

                                        uv_map_nodes = [node for node in node_tree.nodes if node.type == 'UVMAP']

                                        for uv_map_node in uv_map_nodes:
                                            connections = [link.to_socket for link in uv_map_node.outputs[0].links]

                                            # Create a Separate XYZ node
                                            separate_xyz_node = node_tree.nodes.new(type='ShaderNodeSeparateXYZ')
                                            separate_xyz_node.label = "Ping Pong Separate"
                                            separate_xyz_node.location = uv_map_node.location.x, uv_map_node.location.y + 200
                                            node_tree.links.new(uv_map_node.outputs[0], separate_xyz_node.inputs[0])

                                            # Create the first Math node
                                            math_node_1 = node_tree.nodes.new(type='ShaderNodeMath')
                                            math_node_1.operation = 'PINGPONG'
                                            math_node_1.label = "Ping Pong X"
                                            math_node_1.inputs[1].default_value = 1.0
                                            math_node_1.location = separate_xyz_node.location.x + 200, separate_xyz_node.location.y
                                            node_tree.links.new(separate_xyz_node.outputs[0], math_node_1.inputs[0])

                                            # Create the second Math node
                                            math_node_2 = node_tree.nodes.new(type='ShaderNodeMath')
                                            math_node_2.operation = 'PINGPONG'
                                            math_node_2.label = "Ping Pong Y"
                                            math_node_2.inputs[1].default_value = 1.0
                                            math_node_2.location = separate_xyz_node.location.x + 200, separate_xyz_node.location.y - 100
                                            node_tree.links.new(separate_xyz_node.outputs[1], math_node_2.inputs[0])

                                            # Create the Combine XYZ node
                                            combine_xyz_node = node_tree.nodes.new(type='ShaderNodeCombineXYZ')
                                            combine_xyz_node.location = math_node_1.location.x + 200, (math_node_1.location.y + math_node_2.location.y) / 2
                                            combine_xyz_node.label = "Ping Pong Combine"
                                            combine_xyz_node.inputs[2].default_value = 0.0
                                            node_tree.links.new(math_node_1.outputs['Value'], combine_xyz_node.inputs[0])
                                            node_tree.links.new(math_node_2.outputs['Value'], combine_xyz_node.inputs[1])

                                            # Reconnect the original connections to the Combine XYZ node
                                            for socket in connections:
                                                node_tree.links.new(combine_xyz_node.outputs['Vector'], socket)

                                    case "NO_PP":
                                        node_tree = material.node_tree

                                        pp_separate_nodes = [node for node in node_tree.nodes if node.label == 'Ping Pong Separate']

                                        for pp_separate_node in pp_separate_nodes:
                                            in_node = pp_separate_node.inputs[0].links[0].from_node
                                            pp_x_node = pp_separate_node.outputs[0].links[0].to_node
                                            pp_y_node = pp_separate_node.outputs[1].links[0].to_node
                                            pp_combine_node = pp_x_node.outputs[0].links[0].to_node
                                            out_nodes = [link.to_node for link in pp_combine_node.outputs[0].links]

                                            # Reconnect the original connections to the Combine XYZ node
                                            for out_node in out_nodes:
                                                node_tree.links.new(in_node.outputs[0], out_node.inputs[0])

                                            # Remove Ping Pong nodes
                                            node_tree.nodes.remove(pp_x_node)
                                            node_tree.nodes.remove(pp_y_node)
                                            node_tree.nodes.remove(pp_combine_node)
                                            node_tree.nodes.remove(pp_separate_node)

                                num_processed += 1
                    obj.data.update()

        if num_processed != 0:
            display_msg_box(
                f'Applied template to {num_processed} material(s).', 'Info', 'INFO')

        return {'FINISHED'}

# Find Active Face Texture operator

class FindActiveFaceTexture(bpy.types.Operator):
    """Finds the diffuse texture assigned to the current active face, and selects it in the Image Editor"""
    bl_idname = "image.find_active_diffuse"
    bl_label = "Find Active Face Texture"
    bl_options = {'REGISTER'}

    def execute(self, context):

        list_of_mats = check_for_selected()

        # Check if any objects are selected.
        if list_of_mats != False:

            # Get the active object
            obj = bpy.context.active_object
            if obj.type == "MESH":

                # Get active material
                mat = obj.active_material

                node_tree = mat.node_tree

                # Find the diffuse image texture node
                diffuse = None

                for node in node_tree.nodes:
                    if node.type == "TEX_IMAGE":
                        if len(node.outputs[0].links) > 0:

                            for link in node.outputs[0].links:

                                # Check if Image Texture is connected to a "color" socket," or a Mix node's A and B sockets
                                if "Color" in link.to_socket.name or "A" in link.to_socket.name or "B" in link.to_socket.name:
                                    diffuse = node
                                    break

                    # Check if diffuse was found already, and if so, break out of the loop
                    if diffuse != None:
                        break

                # If diffuse was found:
                if diffuse != None:

                    # Find active image editor
                    for screen in bpy.context.screen.areas:
                        if screen.type == "IMAGE_EDITOR":
                            for space in screen.spaces:
                                if space.type == "IMAGE_EDITOR":
                                    space.image = diffuse.image
                        else:
                            continue

                else:
                    display_msg_box(
                        'No texture was found. Make sure the active object has at least 1 material, with at least 1 texture assigned to it. Then go into Edit mode and select a face, then try running the operation again', 'Error', 'ERROR')

        return {'FINISHED'}
    
# Copy Active Face Texture operator

class CopyActiveFaceTexture(bpy.types.Operator):
    """Copies the diffuse texture assigned to the current active face, and stores it for pasting in another face's material"""
    bl_idname = "image.copy_active_diffuse"
    bl_label = "Copy Active Face Texture"
    bl_options = {'REGISTER'}

    def execute(self, context):

        list_of_mats = check_for_selected()

        # Check if any objects are selected.
        if list_of_mats != False:

            # Get the active object
            obj = bpy.context.active_object
            if obj.type == "MESH":

                # Get active material
                mat = obj.active_material

                node_tree = mat.node_tree

                # Find the diffuse image texture node
                diffuse = None

                for node in node_tree.nodes:
                    if node.type == "TEX_IMAGE":
                        if len(node.outputs[0].links) > 0:

                            for link in node.outputs[0].links:

                                # Check if Image Texture is connected to a "color" socket," or a Mix node's A and B sockets
                                if "Color" in link.to_socket.name or "A" in link.to_socket.name or "B" in link.to_socket.name:
                                    
                                    # Check if there's an actual image texture loaded in the node
                                    if node.image:
                                        diffuse = node
                                        break

                    # Check if diffuse was found already, and if so, break out of the loop
                    if diffuse != None:
                        break

                # If diffuse was found:
                if diffuse != None:
                    bpy.context.scene.MatBatchProperties.CopiedTexture = diffuse.image.name
                else:
                    display_msg_box(
                        'No texture was found. Make sure the active object has at least 1 material, with at least 1 texture assigned to it. Then go into Edit mode and select a face, then try running the operation again', 'Error', 'ERROR')

        return {'FINISHED'}

# Paste Active Face Texture operator

class PasteActiveFaceTexture(bpy.types.Operator):
    """Pastes the previously copied diffuse texture into the selected, active face's active material"""
    bl_idname = "image.paste_active_diffuse"
    bl_label = "Paste Active Face Texture"
    bl_options = {'REGISTER'}

    def execute(self, context):

        list_of_mats = check_for_selected()

        # Check if any objects are selected.
        if list_of_mats != False:

            # Get the active object
            obj = bpy.context.active_object
            if obj.type == "MESH":

                # Get active material
                mat = obj.active_material

                node_tree = mat.node_tree

                # Check if a texture was already copied
                copied_tex = bpy.context.scene.MatBatchProperties.CopiedTexture

                if copied_tex != "" and bpy.data.images[copied_tex]:

                    # Find the diffuse image texture node
                    diffuse = None

                    for node in node_tree.nodes:
                        if node.type == "TEX_IMAGE":
                            if len(node.outputs[0].links) > 0:

                                for link in node.outputs[0].links:

                                    # Check if Image Texture is connected to a "color" socket," or a Mix node's A and B sockets
                                    if "Color" in link.to_socket.name or "A" in link.to_socket.name or "B" in link.to_socket.name:
                                        diffuse = node
                                        break

                        # Check if diffuse was found already, and if so, break out of the loop
                        if diffuse != None:
                            break

                    # If diffuse was found:
                    if diffuse != None:
                        diffuse.image = bpy.data.images[copied_tex]
                    else:
                        display_msg_box(
                            'No image texture node was found. Make sure the active object has at least 1 material, with at least 1 image texture node in its node tree.', 'Error', 'ERROR')

        return {'FINISHED'}


# Copy Texture to Material Name operator


class CopyTexToMatName(bpy.types.Operator):
    """Finds the diffuse texture in all materials, in all selected objects, and renames the material to the diffuse's texture name (minus the file extension)"""
    bl_idname = "material.copy_tex_to_mat_name"
    bl_label = "Copy Diffuse Texture to Material Name"
    bl_options = {'REGISTER'}

    def execute(self, context):

        num_processed = 0

        list_of_mats = check_for_selected()

        # Check if any objects are selected.
        if list_of_mats != False:

            # For each selected object
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":

                    # For each material
                    for mat in list_of_mats:

                        if mat in bpy.data.materials.keys():
                            node_tree = bpy.data.materials[mat].node_tree

                            # Find the diffuse image texture node
                            diffuse = None
                            if node_tree != None:
                                for node in node_tree.nodes:

                                    if node.type == "TEX_IMAGE":
                                        # Check if a file is actually loaded in this image texture node
                                        if node.image:

                                            if len(node.outputs[0].links) > 0:

                                                for link in node.outputs[0].links:

                                                    # Check if Image Texture is connected to a "color" socket," or a Mix node's A and B sockets
                                                    if "Color" in link.to_socket.name or "A" in link.to_socket.name or "B" in link.to_socket.name:
                                                        diffuse = node
                                                        break
                                        else:
                                            continue

                                    # Check if diffuse was found already, and if so, break out of the loop
                                    if diffuse != None:

                                        break
                            else:
                                display_msg_box(
                                    'No nodes exist in the active material of this object.', 'Error', 'ERROR')
                                continue

                            # If diffuse was found:
                            if diffuse != None:
                                
                                    # Get the texture name, but without the file extension
                                    diffuse_name = diffuse.image.name.split(".", 1)[0]

                                    # Check if a material with that name already exists
                                    if diffuse_name in bpy.data.materials:
                                        if mat in obj.material_slots.keys():
                                            old_index = obj.material_slots[mat].slot_index
                                            obj.material_slots[old_index].material = bpy.data.materials[diffuse_name]

                                    # If material doesn't exist yet, change the current material's name
                                    else:
                                        if mat in bpy.data.materials.keys():
                                            bpy.data.materials[mat].name = diffuse_name
                                            num_processed += 1

        display_msg_box(
            f'Renamed {num_processed} material(s).', 'Info', 'INFO')

        return {'FINISHED'}


# Isolate by Material Trait operator

class IsolateByMatTrait(bpy.types.Operator):
    """Searches any currently selected meshes for assigned materials with a specific trait, and isolates those polygons into a separate object (and optionally, a dedicated collection)"""
    bl_idname = "material.isolate_by_trait"
    bl_label = "Isolate by Material Trait"
    bl_options = {'REGISTER'}

    def execute(self, context):

        list_of_mats = check_for_selected()
        isolate_to_collection = bpy.context.scene.MatBatchProperties.IsolateCollection
        principled_alpha_slot = 21 if bpy.app.version < (4, 0, 0) else 4
        principled_emissive_color_slot = 19 if bpy.app.version < (4, 0, 0) else 27
        principled_emissive_strength_slot = 20 if bpy.app.version < (4, 0, 0) else 28
        trait = bpy.context.scene.MatBatchProperties.IsolateTrait
        matching_materials = set()
        separated_objs = set()

        root_collection = None

        # Check if any objects are selected.
        if list_of_mats != False:

            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":

                    for mat in list_of_mats:

                        if mat != '':

                            material = bpy.data.materials[mat]
                            material.use_nodes = True

                            if material and material.use_nodes:
                                for node in material.node_tree.nodes:
                                    if is_node_connected(material, node):

                                        if trait == "transparent":
                                            
                                            # Transparency scenario 1 - Principled BSDF with alpha input
                                            if node.type == "BSDF_PRINCIPLED":
                                                if len(node.inputs[principled_alpha_slot].links) > 0 or node.inputs[principled_alpha_slot].default_value != 1:
                                                    matching_materials.add(material.name)
                                                    continue

                                            # Transparency scenario 2 - Transparent BSDF
                                            elif node.type == "BSDF_TRANSPARENT":
                                                    matching_materials.add(material.name)
                                                    continue
                                            
                                        if trait == "emissive":
                                            is_emissive = False

                                            # Emissive scenario 1 - Principled BSDF with emissive input
                                            if node.type == "BSDF_PRINCIPLED":
                                                em_color_slot = node.inputs[principled_emissive_color_slot]
                                                em_strength_slot = node.inputs[principled_emissive_strength_slot]
                                                if em_strength_slot.default_value != 0.0 or len(em_strength_slot.links) > 0:
                                                    if len(em_color_slot.links) > 0:
                                                        is_emissive = True
                                                    elif list(em_color_slot.default_value) != [0.0,0.0,0.0,1.0] and list(em_color_slot.default_value) != [0.0,0.0,0.0,0.0]:
                                                        is_emissive = True

                                            # Emissive scenario 2 - Emission shader
                                            elif node.type == "EMISSION":
                                                is_emissive = True

                                            if is_emissive:
                                                matching_materials.add(material.name)
                                                continue
                    

        materials_matched_count = 0
        if len(matching_materials) > 0:

            # Search all selected mesh objects for faces that have this material assigned.
            mesh_objects = [obj for obj in bpy.context.selected_objects if obj.type == "MESH" and not (obj.name.endswith("_" + trait))]
            if len(mesh_objects) == 0:
                display_msg_box(
                    f'Selected trait has already been fully isolated in the selected object(s).', 'Info', 'INFO')
                return {'FINISHED'}
            
            bpy.ops.object.select_all(action='DESELECT')
            for obj in mesh_objects:
                obj.hide_set(False)
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj

                matching_faces = set()
                for material in matching_materials:
                    material_matched = False
                    for face_index in find_faces_with_material(obj, material):
                        matching_faces.add(face_index)
                        material_matched = True
                    if material_matched:
                        materials_matched_count += 1

                if len(matching_faces) > 0:
                    if len(obj.data.polygons) == len(matching_faces):
                        continue
                    separated_obj = separate_faces(obj, matching_faces)
                    separated_obj.name = obj.name + "_" + trait

                    separated_objs.add(separated_obj)
            
            if isolate_to_collection:
                if trait.capitalize() in bpy.data.collections.keys():
                    root_collection = bpy.data.collections[trait.capitalize()]
                else:
                    root_collection = bpy.data.collections.new(trait.capitalize())
                    bpy.context.scene.collection.children.link(root_collection)

                for obj in separated_objs:
                    # Unlink the new collision model from other collections
                    obj_collections = [
                        c for c in bpy.data.collections if obj.name in c.objects.keys()]
                    for c in obj_collections:
                        if obj.name in c.objects.keys():
                            c.objects.unlink(obj)
                    if obj.name in bpy.context.scene.collection.objects.keys():
                        bpy.context.scene.collection.objects.unlink(obj)

                    root_collection.objects.link(obj)
                    bpy.context.view_layer.objects.active = obj
                    obj.select_set(True)

        display_msg_box(
            f'Isolated {materials_matched_count} {trait} material(s) into {len(separated_objs)} separate object(s).', 'Info', 'INFO')
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
    self.layout.operator(SetAsTemplateNode.bl_idname)
    self.layout.operator(UnifyNodeSettings.bl_idname)
    self.layout.operator(SwitchShader.bl_idname)
    self.layout.operator(ApplyMatTemplate.bl_idname)
    self.layout.operator(FindActiveFaceTexture.bl_idname)
    self.layout.operator(CopyTexToMatName.bl_idname)
    self.layout.operator(IsolateByMatTrait.bl_idname)


def imageeditor_menu_func(self, context):
    self.layout.operator(FindActiveFaceTexture.bl_idname)
    self.layout.operator(CopyActiveFaceTexture.bl_idname)
    self.layout.operator(PasteActiveFaceTexture.bl_idname)
    self.layout.operator(CopyTexToMatName.bl_idname)
    
# MATERIALS PANEL


class MaterialBatchToolsPanel(bpy.types.Panel):
    bl_label = 'Material Batch Tools'
    bl_idname = "MATERIAL_PT_matbatchtools"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'

    @ classmethod
    def poll(cls, context):
        return (context.object != None)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        layout.enabled = (len(bpy.context.selected_objects) > 0)

class MaterialBatchToolsSubPanel_Nodes(bpy.types.Panel):
    bl_parent_id = "MATERIAL_PT_matbatchtools"
    bl_label = 'Nodes'
    bl_idname = "MATERIAL_PT_matbatchtools_nodes"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_options = {"DEFAULT_CLOSED"}
    bl_context = 'material'

    @ classmethod
    def poll(cls, context):
        return (context.object != None)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout

        # Node Unify UI
        boxUnify = layout.box()
        boxUnify.label(text="Node Unify")
        rowUnify1 = boxUnify.row()
        rowUnify1.label(text="Saved Node: " +
                        bpy.context.scene.MatBatchProperties.SavedNodeType)
        rowUnify2 = boxUnify.row()
        rowUnify3 = boxUnify.row()
        rowUnify4 = boxUnify.row()

        rowUnify2.prop(
            bpy.context.scene.MatBatchProperties, "UnifyFilterLabel")
        rowUnify3.operator("material.set_as_template_node")
        rowUnify4.operator("material.unify_node_settings")
        rowUnify4.enabled = (
            bpy.context.scene.MatBatchProperties.SavedNodeName != "")

        layout.separator()

        # Bake Target Node UI
        boxBakeTarget = layout.box()
        boxBakeTarget.label(text="Bake Target Node")

        rowBakeTarget0 = boxBakeTarget.row()
        rowBakeTarget1 = boxBakeTarget.row()
        rowBakeTarget2 = boxBakeTarget.row()

        rowBakeTarget0.operator("material.copy_bake_target")
        rowBakeTarget0.operator("material.paste_bake_target")
        rowBakeTarget1.operator("material.delete_bake_target")
        rowBakeTarget2.prop(
            bpy.context.scene.MatBatchProperties, "BakeTargetNodeColorEnable")
        rowBakeTarget2.prop(
            bpy.context.scene.MatBatchProperties, "BakeTargetNodeColor")

        layout.separator()

        # Material Template UI
        boxTemplate = layout.box()
        boxTemplate.label(text="Material Templates")
        rowSwitchShader1 = boxTemplate.row()
        rowSwitchShader2 = boxTemplate.row()
        rowTemplate1 = boxTemplate.row()
        rowTemplate2 = boxTemplate.row()
        rowTemplate3 = boxTemplate.row()

        rowSwitchShader1.prop(
            bpy.context.scene.MatBatchProperties, "SwitchShaderTarget")
        rowSwitchShader2.operator("material.switch_shader")

        rowTemplate1.prop(bpy.context.scene.MatBatchProperties, "Template")
        rowTemplate2.prop(bpy.context.scene.MatBatchProperties, "SkipTexture")
        rowTemplate3.operator("material.apply_mat_template")

class MaterialBatchToolsSubPanel_Transparency(bpy.types.Panel):
    bl_parent_id = "MATERIAL_PT_matbatchtools"
    bl_label = 'Transparency'
    bl_idname = "MATERIAL_PT_matbatchtools_transparency"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_options = {"DEFAULT_CLOSED"}
    bl_context = 'material'

    @ classmethod
    def poll(cls, context):
        return (context.object != None)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout

        # Transparency UI
        boxTransparency = layout.box()
        rowTransparency1 = boxTransparency.row()
        rowTransparency2 = boxTransparency.row()
        rowTransparency3 = boxTransparency.row()
        rowTransparency4 = boxTransparency.row()
        rowTransparency5 = boxTransparency.row()
        rowTransparency1.prop(
            bpy.context.scene.MatBatchProperties, "AlphaBlendMode")
        rowTransparency2.prop(bpy.context.scene.MatBatchProperties,
                              "AlphaBlendFilter")
        rowTransparency3.prop(bpy.context.scene.MatBatchProperties,
                              "AlphaThreshold")
        rowTransparency3.enabled = (
            bpy.context.scene.MatBatchProperties.AlphaBlendMode == "CLIP")
        rowTransparency4.prop(
            bpy.context.scene.MatBatchProperties, "AlphaPrincipledRemove")
        rowTransparency4.enabled = (
            bpy.context.scene.MatBatchProperties.AlphaBlendMode == "OPAQUE")
        rowTransparency5.operator("material.set_blend_mode")

class MaterialBatchToolsSubPanel_UV_VC(bpy.types.Panel):
    bl_parent_id = "MATERIAL_PT_matbatchtools"
    bl_label = 'UV & Vertex Colors'
    bl_idname = "MATERIAL_PT_matbatchtools_uv_vc"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_options = {"DEFAULT_CLOSED"}
    bl_context = 'material'

    @ classmethod
    def poll(cls, context):
        return (context.object != None)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout

        # UV Map Node UI
        boxUVMap1 = layout.box()
        rowUVMap1 = boxUVMap1.row()
        rowUVMap2 = boxUVMap1.row()
        rowUVMap3 = boxUVMap1.row()

        rowUVMap1.prop(bpy.context.scene.MatBatchProperties,
                       "UVMapNodeTarget")
        rowUVMap2.prop(bpy.context.scene.MatBatchProperties,
                       "UVMapNodeExtensionFilter")
        rowUVMap3.operator("material.assign_uv_map_node")

        boxUVMap2 = boxUVMap1.box()
        rowUVMap4 = boxUVMap2.row()
        rowUVMap5 = boxUVMap2.row()
        rowUVMap6 = boxUVMap2.row()

        # UV Slot UI
        rowUVMap4.prop(bpy.context.scene.MatBatchProperties, "UVSlotIndex")
        rowUVMap5.operator("object.overwrite_uv_slot_name")
        rowUVMap6.operator("object.set_uv_slot_as_active")\

        layout.separator()

        # Vertex Colors UI
        boxVertexColors = layout.box()
        boxVertexColors.label(text="Vertex Colors")
        rowVertexColors1 = boxVertexColors.row()
        rowVertexColors2 = boxVertexColors.row()
        rowVertexColors3 = boxVertexColors.row()
        rowVertexColors4 = boxVertexColors.row()

        rowVertexColors1.prop(bpy.context.scene.MatBatchProperties, "VCName")
        rowVertexColors2.operator("material.assign_vc_to_nodes")
        rowVertexColors3.operator("object.rename_vertex_color")
        rowVertexColors4.operator("object.convert_vertex_color")

class MaterialBatchToolsSubPanel_Isolate(bpy.types.Panel):
    bl_parent_id = "MATERIAL_PT_matbatchtools"
    bl_label = 'Isolate'
    bl_idname = "MATERIAL_PT_matbatchtools_isolate"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_options = {"DEFAULT_CLOSED"}
    bl_context = 'material'

    @ classmethod
    def poll(cls, context):
        return (context.object != None)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout

        # UV Map Node UI
        boxIsolate = layout.box()
        rowIsolate1 = boxIsolate.row()
        rowIsolate2 = boxIsolate.row()
        rowIsolate3 = boxIsolate.row()

        rowIsolate1.prop(bpy.context.scene.MatBatchProperties, "IsolateCollection")
        rowIsolate2.prop(bpy.context.scene.MatBatchProperties, "IsolateTrait")
        rowIsolate3.operator("material.isolate_by_trait")


# End of classes


classes = (
    MatBatchProperties,
    CopyBakeTargetNode,
    PasteBakeTargetNode,
    DeleteBakeTargetNode,
    AssignUVMapNode,
    OverwriteUVSlotName,
    SetUVSlotAsActive,
    AssignVCToNodes,
    RenameVertexColorSlot,
    ConvertVertexColor,
    SetBlendMode,
    SetAsTemplateNode,
    UnifyNodeSettings,
    SwitchShader,
    ApplyMatTemplate,
    FindActiveFaceTexture,
    CopyActiveFaceTexture,
    PasteActiveFaceTexture,
    CopyTexToMatName,
    IsolateByMatTrait,
    MaterialBatchToolsPanel,
    MaterialBatchToolsSubPanel_Nodes,
    MaterialBatchToolsSubPanel_UV_VC,
    MaterialBatchToolsSubPanel_Transparency,
    MaterialBatchToolsSubPanel_Isolate
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.MatBatchProperties = bpy.props.PointerProperty(
        type=MatBatchProperties)

    bpy.types.IMAGE_MT_image.append(imageeditor_menu_func)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.MatBatchProperties


if __name__ == "__main__":
    register()
