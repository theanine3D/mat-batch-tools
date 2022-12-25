# mat-batch-tools
Addon for Blender that allows batch modification of many materials and nodes simultaneously, and automates common repetitive tasks on models with many materials

Features:
- Bake Target Node - Copy / paste your own customized Image Texture node into all materials on all selected objects.
	- The created Image Texture node is set as "active" automatically, making it ready as a target for baking
	- Optional color setting allows you to add a color decoration to the node, making it easier to identify
- Rename UV maps and vertex colors on all selected objects at once
- Add and connect a UV Map node (with a specific UV Map set) to all Image Texture nodes, in all materials in all selected objects at once
- Switch the Blend Mode and Shadow Mode between Opaque, Alpha Clip, and Alpha Blend, in all materials on all selected objects, with an optional filter based on the shader (Principled BSDF or Transparent BSDF) present in the material

![image](https://user-images.githubusercontent.com/88953117/209455390-b8bcaa51-363e-462a-ba9f-5e0dbb41e6cc.png)
