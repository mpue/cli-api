# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import bpy
import os
import random
import sys
import argparse


bl_info = {
    "name": "Package Generator",
    "author": "Matthias Pueski",
    "description": "",
    "blender": (2, 80, 0),
    "version": (0, 0, 1),
    "location": "",
    "warning": "",
    "category": "Generic",
}

class PackageGeneratorPanel(bpy.types.Panel):
    bl_label = "Package Generator"
    bl_idname = "OBJECT_PT_package_generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "PackageGen"

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "package_width")
        layout.prop(context.scene, "package_height")
        layout.prop(context.scene, "package_depth")
        layout.prop(context.scene, "package_random_factor")
        layout.prop(context.scene, "package_subdivisions")
        layout.prop(context.scene, "package_deformation_strength")
        layout.prop(context.scene, "package_texture")
        layout.operator("mesh.generate_package", text="Generate Package")

class GeneratePackageOperator(bpy.types.Operator):
    bl_idname = "mesh.generate_package"
    bl_label = "Generate Package"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        generate_package()
        return {'FINISHED'}

def generate_package(args):
    '''
    width = bpy.context.scene.package_width * random.uniform(1.0 - bpy.context.scene.package_random_factor, 1.0 + bpy.context.scene.package_random_factor)
    height = bpy.context.scene.package_height * random.uniform(1.0 - bpy.context.scene.package_random_factor, 1.0 + bpy.context.scene.package_random_factor)
    depth = bpy.context.scene.package_depth * random.uniform(1.0 - bpy.context.scene.package_random_factor, 1.0 + bpy.context.scene.package_random_factor)
    '''

    bpy.ops.mesh.primitive_cube_add()
    package = bpy.context.object
    package.scale = (args.pwidth / 2, args.pdepth / 2, args.pheight / 2)
    package.name = "GeneratedPackage"

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=bpy.context.scene.package_subdivisions)
    bpy.ops.object.mode_set(mode='OBJECT')

    bevel_modifier = package.modifiers.new(name="Bevel", type='BEVEL')
    bevel_modifier.width = 0.1
    bevel_modifier.segments = 3

    modifier = package.modifiers.new(name="Displacement", type='DISPLACE')
    texture = bpy.data.textures.new(name="NoiseTexture", type='CLOUDS')
    modifier.texture = texture
    modifier.strength = bpy.context.scene.package_deformation_strength

    bpy.ops.object.shade_smooth()

    mat = bpy.data.materials.get("PackageMaterial")
    if mat is None:
        mat = bpy.data.materials.new(name="PackageMaterial")
        mat.use_nodes = True

    if package.data.materials:
        package.data.materials[0] = mat
    else:
        package.data.materials.append(mat)

    if bpy.context.scene.package_texture and os.path.exists(bpy.context.scene.package_texture):
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            tex_node = mat.node_tree.nodes.new("ShaderNodeTexImage")
            tex_node.image = bpy.data.images.load(bpy.context.scene.package_texture)
            mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_node.outputs['Color'])

def export_gltf(filepath):
    for mat in bpy.data.materials:
        if mat.use_nodes:
            for node in mat.node_tree.nodes:
                if isinstance(node, bpy.types.ShaderNodeTexImage) and node.image:
                    node.image.pack()
    
    bpy.ops.export_scene.gltf(filepath=filepath, export_format="GLB", export_apply=True)

def export_usd(filepath):
    for mat in bpy.data.materials:
        if mat.use_nodes:
            for node in mat.node_tree.nodes:
                if isinstance(node, bpy.types.ShaderNodeTexImage) and node.image:
                    node.image.pack()

    bpy.ops.wm.usd_export(filepath=filepath, export_textures=True)

def renderAndSaveImage():
    bpy.context.scene.render.filepath = "/data/uploads/output.png"
    bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'  # Alternative: 'OPTIX' or 'HIP' for AMD
    bpy.context.scene.cycles.device = 'GPU'

    # render settings    
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    bpy.context.scene.render.resolution_percentage = 100

    bpy.ops.render.render(write_still=True)

# Register properties

bpy.types.Scene.package_width = bpy.props.FloatProperty(name="Package Width", default=2.0, min=0.1, max=10.0)
bpy.types.Scene.package_height = bpy.props.FloatProperty(name="Package Height", default=2.0, min=0.1, max=10.0)
bpy.types.Scene.package_depth = bpy.props.FloatProperty(name="Package Depth", default=2.0, min=0.1, max=10.0)
bpy.types.Scene.package_random_factor = bpy.props.FloatProperty(name="Random Factor", default=0.1, min=0.0, max=1.0)
bpy.types.Scene.package_subdivisions = bpy.props.IntProperty(name="Subdivisions", default=2, min=0, max=10)
bpy.types.Scene.package_deformation_strength = bpy.props.FloatProperty(name="Deformation Strength", default=0.1, min=0.0, max=1.0)
bpy.types.Scene.package_texture = bpy.props.StringProperty(name="Texture Path", subtype='FILE_PATH')

def parse_args():
    parser = argparse.ArgumentParser(description='Blender Render Script')
    parser.add_argument('--pwidth', type=float, required=True, help='Package width')
    parser.add_argument('--pheight', type=float, required=True, help='Package height')
    parser.add_argument('--pdepth', type=float, required=True, help='Package depth')
    # Filter out Blender's own arguments: only consider args after '--'
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    args = parser.parse_args(argv)
    return args



# Register classes
def register():
    bpy.utils.register_class(PackageGeneratorPanel)
    bpy.utils.register_class(GeneratePackageOperator)

def unregister():
    bpy.utils.unregister_class(PackageGeneratorPanel)
    bpy.utils.unregister_class(GeneratePackageOperator)
    del bpy.types.Scene.package_width
    del bpy.types.Scene.package_height
    del bpy.types.Scene.package_depth
    del bpy.types.Scene.package_random_factor
    del bpy.types.Scene.package_subdivisions
    del bpy.types.Scene.package_deformation_strength
    del bpy.types.Scene.package_texture

if __name__ == "__main__":
    register()
    # if '--run' in sys.argv:
    args = parse_args()
    generate_package(args)
    export_usd("/data/uploads/package.usda")
    renderAndSaveImage()
    bpy.ops.wm.quit_blender()
