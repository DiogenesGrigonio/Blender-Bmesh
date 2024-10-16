# GPL # (c) 2024 Diogenes Grigonio
# mesh operator

import bpy, bmesh, random


class BASIC_OT_bmeshCreateWindow(bpy.types.Operator):
    """Create an object for use in Dirt Calculation"""
    bl_idname = "basic.create_window"
    bl_label = "Create Window"
    bl_options = {"REGISTER", "UNDO"}
    
    amount_light = bpy.props.IntProperty(
            name="Amount Light:",
            default=25,
            min=10,
            max=100,
            subtype='PERCENTAGE')

    amount_curtain = bpy.props.IntProperty(
            name="Amount Curtain:",
            default=25,
            min=0,
            max=75,
            subtype='PERCENTAGE')

    seed = bpy.props.IntProperty(
            name="Seed:",
            default=50,
            min=1)

    thick = bpy.props.FloatProperty(
            name="Thickness:",
            default=0.35,
            min=0.25,
            subtype='DISTANCE')
            
    resolution = bpy.props.IntProperty(
            name="Resolution Curtain:",
            default=6,
            min=2, 
            max=18)

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
        Thick = self.thick
        CurtainResol = self.resolution
        SelfSeed = self.seed

        #Get Materials
        Mat = context.object.data.materials
        Name = context.object.name.split(':')[0]
        Mat.append(data.materials[Name+":thin_RAY.002_DRV"])
        Mat.append(data.materials["001.non_material.000"])
        Mat.append(data.materials[Name+":luz_INTERNA.01"])
        Mat.append(data.materials[Name+":luz_INTERNA.02"])
        Mat.append(data.materials[Name+":luz_INTERNA.03"])
        Mat.append(data.materials["001.curtain.000"])
        
        #Create BlackBox
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

        #Apply Material in BlackBox
        BMesh.select_mode = {'EDGE'}
        for face in NewFaces['faces']:
            for vert in face.verts:
                for edge in vert.link_edges:edge.select_set(True)
        BMesh.select_flush(True)
        BlackBoxFaces = [face for face in BMesh.faces if face.select]
        for face in BlackBoxFaces:face.material_index = 1

        #Get Faces
        Faces = [face for face in BMesh.faces if face not in BlackBoxFaces]

        #create Face List for Curtains - 'FaceCurtains'
        FaceToCurtains = Faces.copy()
        for i in range(int(len(FaceToCurtains)*AmountCurtain)):
            random.seed(SelfSeed+i)
            RandomElement = random.choice(FaceToCurtains)
            del FaceToCurtains[FaceToCurtains.index(RandomElement)]
            
        #Create Curtains
        VertsCurtain = []
        FacesCurtain = []

        for FaceCurtain in FaceToCurtains:
            if len(FaceCurtain.verts)==4:
                NorX = FaceCurtain.normal[0]
                NorY = FaceCurtain.normal[1]
                VerticeGroup = [vert.co for vert in FaceCurtain.verts]
                AxisZ = min([vert[2] for vert in VerticeGroup])
                SizeZ = max([vert[2] for vert in VerticeGroup]) - AxisZ
                VerticesZ = [v for v in FaceCurtain.verts if v.co[2]==AxisZ]
                SizeL = abs(VerticesZ[0].co[0] - VerticesZ[1].co[0])
                DirL = VerticesZ[1].co - VerticesZ[0].co
                
                VertX = VerticesZ[0].co[0]
                if round(DirL[1], 3)>=0:
                    VertY = min([VerticesZ[0].co[1], VerticesZ[1].co[1]])
                else:
                    VertY = max([VerticesZ[0].co[1], VerticesZ[1].co[1]])
                VertZ = VerticesZ[0].co[2]-0.01

                Vert0Co = [VertX, VertY, VertZ]
                VertCurtainLow = []
                VertCurtainHigh = []

                for i in range(CurtainResol):
                    i = bmesh.ops.create_vert(BMesh,co=Vert0Co)
                    V = i['vert'][0]
                    VertCurtainLow.append(V)

                Loc=1/24
                for v in VertCurtainLow[1:]:
                    bmesh.ops.translate(
                        BMesh, verts = [v], 
                        vec=(DirL[0]*Loc, 
                        DirL[1]*Loc, 0)
                        )
                    Loc+=random.uniform(1/24, 2/12)
                for v in VertCurtainLow:
                    bmesh.ops.translate(
                        BMesh, 
                        verts = [v], 
                        vec=(-NorX*random.uniform(0.01, Thick/3.5), 
                            -NorY*random.uniform(0.01, Thick/3.5), 
                            0))

                Vert0Co[2] = VertZ+SizeZ+0.01

                for i in range(CurtainResol):
                    i = bmesh.ops.create_vert(BMesh,co=Vert0Co)
                    V = i['vert'][0]
                    VertCurtainHigh.append(V)

                Loc=1/24
                for v in VertCurtainHigh[1:]:
                    bmesh.ops.translate(
                        BMesh, 
                        verts = [v], 
                        vec=(DirL[0]*Loc, DirL[1]*Loc, 0))
                    Loc+=random.uniform(1/24, 2/12)
                    
                for v in VertCurtainHigh:
                    bmesh.ops.translate(
                        BMesh, 
                        verts = [v], 
                        vec=(-NorX*random.uniform(0.01, Thick/3.5), 
                            -NorY*random.uniform(0.01, Thick/3.5), 
                            0))

                VertsCurtain.extend(VertCurtainHigh)
                VertsCurtain.extend(VertCurtainLow)

                for i in range(CurtainResol-1):
                    face = BMesh.faces.new([
                                    VertCurtainLow[0+i], 
                                    VertCurtainLow[1+i], 
                                    VertCurtainHigh[1+i], 
                                    VertCurtainHigh[0+i]])
                    FacesCurtain.append(face)

        #Apply Material and Smooth in Curtains
        for face in FacesCurtain:
            face.material_index = 5
            face.smooth = True

        #create Light INT
        for i in range(int(len(Faces)*AmountLight)):
            random.seed(SelfSeed+i+1)
            RandomElement = random.choice(Faces)
            del Faces[Faces.index(RandomElement)]
            
        for f in Faces:f.copy(verts=True, edges=True)

        for Face in Faces:
            NormalX = Face.normal[0]*Thick/3
            NormalY = Face.normal[1]*Thick/3
            for vert in [v for v in Face.verts]:
                bmesh.ops.translate(
                    BMesh, 
                    vec = (-NormalX, -NormalY, 0),
                    verts = [vert])

        #Apply Materials in Light INT
        for Face in Faces:Face.material_index = 2
        for Face in Faces[::2]:Face.material_index = 3
        for Face in Faces[::3]:Face.material_index = 4

        #Create list of Verts to aplly Mask Modifier
        FaceGlass = [f for f in BMesh.faces 
                    if f not in Faces 
                    and f not in BlackBoxFaces]
                    
        BMesh.verts.ensure_lookup_table()
        
        VertsGlass=[]
        for face in FaceGlass:
            for v in face.verts:
                if v not in VertsCurtain:
                    #v.hide_set(True)
                    VertsGlass.append(v.index)

        #BMesh End
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

        return {"FINISHED"}
