# Material Batch Tools
Addon for Blender that allows batch modification of many materials and nodes simultaneously, and automates common repetitive tasks on models with many materials. Very useful for baking many textures into one - such as with megatextures, texture atlases, etc.

## Features:
- Bake Target Node - Copy / paste your own customized Image Texture node into all materials on all selected objects.
	- The created Image Texture node is set as "active" automatically, making it ready as a target for baking
	- The node is always positioned automatically to the right of the Material Output node, for easy finding
	- Optional color setting allows you to add a color decoration to the node, making it easier to identify
- Rename UV maps and vertex colors on all selected objects at once
- Add and connect a UV Map node (with a specific UV Map set) to all Image Texture nodes, in all materials in all selected objects at once
- Switch the Blend Mode and Shadow Mode between Opaque, Alpha Clip, and Alpha Blend, in all materials on all selected objects, with an optional filter based on the shader (Principled BSDF or Transparent BSDF) present in the material

## Installation
1. Download [mat_batch_tools.py](https://github.com/theanine3D/mat-batch-tools/raw/main/mat_batch_tools.py) (right click this link and Save As...)
2. Go into Blender's addon preferences (File → Preferences → Addons)
3. Click the "Install..." button and browse to mat_batch_tools.py, select it, and press "Install Add-on"

## Notes
Not every function in this addon is undoable. Keep a backup copy of your blend file just in case you need to restore something.

## Previews:
#### The interface - found in the Material Properties tab
![image](https://user-images.githubusercontent.com/88953117/209455390-b8bcaa51-363e-462a-ba9f-5e0dbb41e6cc.png)

#### Automatic creation, assignment, and linking of UV Map nodes for all Image Textures:
![uvmap](https://user-images.githubusercontent.com/88953117/209455488-7ef92550-09c1-439a-ae89-39ad8fc48348.gif)

#### Bake Target
![bake target](https://user-images.githubusercontent.com/88953117/209455528-a3690ce7-2004-47b0-acf5-56c7c9eac398.gif)
