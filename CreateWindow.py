# GPL # (c) 2024 Diogenes Grigonio
# mesh operator

import bpy, bmesh, random, math
from .bmesh_ops import curtains


class BASIC_OT_bmeshCreateWindow(bpy.types.Operator):
    """Create an object for use in Dirt Calculation"""
    bl_idname = "basic.create_window"
    bl_label = "Create Window"
    bl_options = {"REGISTER", "UNDO"}
    
    amount_light = bpy.props.IntProperty(
            name="Amount Light:",
            default=40,
            min=10,
            max=100,
            subtype='PERCENTAGE')

    amount_curtain = bpy.props.IntProperty(
            name="Amount Curtain:",
            default=50,
            min=0,
            max=100,
            subtype='PERCENTAGE')

    seed = bpy.props.IntProperty(
            name="Seed:",
            default=50,
            min=1)
            
    resolution = bpy.props.IntProperty(
            name="Resolution Curtain:",
            default=32,
            min=2, 
            max=64)
            
    type = bpy.props.EnumProperty(
            name="Curtain Type:",
            items = (
            ("TYPE1", "Type1", ""),
            ("TYPE2", "Type2", ""),
            ("BOTH", "Both", ""),
            ),
            default = "BOTH")

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob and ob.type == 'MESH' and context.mode == 'OBJECT'
    
    def execute(self, context):
        
        #BMesh Start
        BMesh = bmesh.new()
        BMesh.from_mesh(context.object.data)

        #Variables
        data = bpy.data
        AmountLight = 1 - (self.amount_light/100)
        AmountCurtain = 1 - (self.amount_curtain/100)
        Thick = 0.35
        CurtainResol = self.resolution
        SelfSeed = self.seed

        #Get Materials
        GetMat = context.object.data.materials
        Name = context.object.name.split(':')[0]
        Material = [[Name+":thin_RAY.002_DRV"],["001.non_material.000"],
                    [Name+":luz_INTERNA.01"], [Name+":luz_INTERNA.02"], 
                    [Name+":luz_INTERNA.03"], ["001.curtain.000"], ["N6"]]
        for mat in Material:
            GetMat.append(data.materials[mat[0]])
    
        """BlackBox"""
        #Create 
        Faces = [f for f in BMesh.faces]
        for f in Faces:f.copy(verts=True, edges=True)
        NewFaces = bmesh.ops.extrude_discrete_faces(
                BMesh,
                faces = Faces)
        for Face in NewFaces['faces']:
            NormalX = Face.normal[0]*Thick
            NormalY = Face.normal[1]*Thick
            for vert in [v for v in Face.verts]:
                bmesh.ops.translate(
                    BMesh, 
                    vec = (-NormalX, -NormalY, 0),
                    verts = [vert])

        #Apply Material (BlackBox)
        BMesh.select_mode = {'EDGE'}
        for face in NewFaces['faces']:
            for vert in face.verts:
                for edge in vert.link_edges:edge.select_set(True)
        BMesh.select_flush(True)
        BlackBoxFaces = [face for face in BMesh.faces if face.select]
        for face in BlackBoxFaces:face.material_index = 1
        Faces = [face for face in BMesh.faces 
                if face not in BlackBoxFaces]
        BMesh.select_mode = {'FACE'}
        for f in BMesh.faces:f.select_set(False)
        BMesh.select_flush(False)

        """Light INT"""
        ##create Face List - 'FacesLightIn'
        FacesLightIn = Faces.copy()
        for i in range(int(len(FacesLightIn)*AmountLight)):
            random.seed(SelfSeed+i+1)
            RandomElement = random.choice(FacesLightIn)
            del FacesLightIn[FacesLightIn.index(RandomElement)]
        for f in FacesLightIn:f.copy(verts=True, edges=True)
        for Face in FacesLightIn:
            NormalX = Face.normal[0]*Thick/3
            NormalY = Face.normal[1]*Thick/3
            for vert in [v for v in Face.verts]:
                bmesh.ops.translate(
                    BMesh, 
                    vec = (-NormalX, -NormalY, 0),
                    verts = [vert])

        #Apply Materials
        for Face in FacesLightIn:Face.material_index = 2
        for Face in FacesLightIn[::2]:Face.material_index = 3
        for Face in FacesLightIn[::3]:Face.material_index = 4

        #Get Faces
        Faces = [face for face in BMesh.faces 
                if face not in BlackBoxFaces 
                and face not in FacesLightIn]

        """Curtains"""
        #create Face List for Curtains - 'FaceToCurtains'
        FaceToCurtains = Faces.copy()
        for i in range(int(len(FaceToCurtains)*AmountCurtain)):
            random.seed(SelfSeed+i)
            RandomElement = random.choice(FaceToCurtains)
            del FaceToCurtains[FaceToCurtains.index(RandomElement)]

        #create Curtains
        if self.type=="TYPE1":
            FaceCurtain = curtains(BMesh, FaceToCurtains, 1, 
                                    CurtainResol, SelfSeed)
            for face in FaceCurtain:face.material_index = 6

        elif self.type=="TYPE2":
            FaceCurtain = curtains(BMesh, FaceToCurtains, 2, 
                                    CurtainResol, SelfSeed)
            for face in FaceCurtain:face.material_index = 5

        elif self.type=="BOTH":
            FaceToCurtains1 = FaceToCurtains.copy()
            for i in range(int(len(FaceToCurtains1)*0.5)):
                random.seed(SelfSeed+i+1)
                RandomElement = random.choice(FaceToCurtains1)
                del FaceToCurtains1[FaceToCurtains1.index(RandomElement)]
            FaceCurtain1 = curtains(BMesh, FaceToCurtains1, 1, 
                                    CurtainResol, SelfSeed)
            FaceToCurtains2 = [f for f in FaceToCurtains 
                                if f not in FaceToCurtains1]
            FaceCurtain2 = curtains(BMesh, FaceToCurtains2, 2, 
                                    CurtainResol, SelfSeed)
            for face in FaceCurtain2:
                face.material_index = 5
            for face in FaceCurtain1:
                face.material_index = 6
                face.smooth = False
        
        #Calculate Normals
        FacesCurtain = [f for f in BMesh.faces
                        if f not in Faces
                        and f not in FacesLightIn
                        and f not in BlackBoxFaces]
        bmesh.ops.recalc_face_normals(BMesh, faces=FacesCurtain)
                
        #Mask Modifier
        BMesh.verts.ensure_lookup_table()
        VertsGlass=[]
        for face in Faces:
            for v in face.verts:
                v.hide_set(True)
                VertsGlass.append(v.index)

        #BMesh End
        for f in BMesh.faces:f.select_set(False)
        BMesh.select_flush(False)
        BMesh.to_mesh(context.object.data)
        BMesh.free()
        context.object.data.update()

        #Create Modifier Mask and apply to Glass
        context.object.vertex_groups.new(name="Glass")
        for v in VertsGlass:
            context.object.vertex_groups['Glass'].add([v], 1, 'ADD')
        MaskGlass = context.object.modifiers.new('MaskGlass', type='MASK')
        MaskGlass.vertex_group='Glass'
        MaskGlass.invert_vertex_group=True
        MaskGlass.show_render=False
        MaskGlass.show_in_editmode = True

        #Apply Smooth
        context.object.data.use_auto_smooth = True
        context.object.data.auto_smooth_angle = math.radians(60)

        return {"FINISHED"}
