# GPL # (c) 2024 Diogenes Grigonio
# mesh operator

import bpy, bmesh


class BASIC_OT_bmeshCreatePot(bpy.types.Operator):
    """Create Pot"""
    bl_idname = "basic.create_pot"
    bl_label = "Create Pot"
    bl_options = {"REGISTER", "UNDO"}

    size = bpy.props.FloatProperty(
            name="Size:",
            default=0.70)

    shape_width = bpy.props.FloatProperty(
            name="Shape Width:",
            default=0.50)

    shape_height = bpy.props.FloatProperty(
            name="Shape Height:",
            default=0.15)

    top_width = bpy.props.FloatProperty(
            name="Top Width:",
            default=0.20)

    base_width = bpy.props.FloatProperty(
            name="Base Width:",
            default=0.20)

    resolution = bpy.props.IntProperty(
            name="Resolution:",
            default=12,
            min=3, 
            max=24)

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'
    
    def execute(self, context):

        #variables
        data = bpy.data
        Resolution = self.resolution
        VertBaseCo = (self.base_width, 0.0, 0.0)
        VertTopCo = (self.top_width, 0.0, self.size)
        VertShapeCo = (self.shape_width, 0.0, self.shape_height)

        #name
        Copies = [n for n in data.objects if 'Pot' in n.name]
        Name = "Pot_" + str("{:0>2}".format(len(Copies)+1))

        #BMesh Start
        BMesh = bmesh.new()

        #Create VertBase
        v = bmesh.ops.create_vert(BMesh,co=VertBaseCo)
        VertBase = v['vert'][0]

        #Create VertTop
        v = bmesh.ops.create_vert(BMesh,co=VertTopCo)
        VertTop = v['vert'][0]

        #Create VertShape
        v = bmesh.ops.create_vert(BMesh,co=VertShapeCo)
        VertShape = v['vert'][0]

        #Create Edges
        BMesh.edges.new((VertTop, VertShape))
        BMesh.edges.new((VertShape,VertBase))

        #BMesh end
        MeshData = data.meshes.new(name=Name)
        BMesh.to_mesh(MeshData)
        BMesh.free()

        #insere o Object na Scene
        Object = data.objects.new(Name, MeshData)
        context.scene.objects.link(Object)

        #seleciona e deixa o Object ativo
        context.scene.objects.active = Object
        Object.select = True

        #Create Screw Modifier
        context.object.modifiers.new('Screw', type='SCREW')
        context.object.modifiers['Screw'].steps = Resolution
        context.object.modifiers['Screw'].render_steps = Resolution

        #Create Screw Modifier
        context.object.modifiers.new('Solidify', type='SOLIDIFY')
        context.object.modifiers['Solidify'].thickness = 0.05
        context.object.modifiers['Solidify'].edge_crease_outer = 1.0
        context.object.modifiers['Solidify'].edge_crease_inner = 1.0
        context.object.modifiers['Solidify'].use_even_offset = True
        context.object.modifiers['Solidify'].use_quality_normals = True

        #Create SubSurface Modifier
        context.object.modifiers.new('SubSurf', 'SUBSURF')
        context.object.modifiers['SubSurf'].levels=2
        context.object.modifiers['SubSurf'].render_levels=3
        
        return {"FINISHED"}
