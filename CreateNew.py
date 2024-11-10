# GPL # (c) 2024 Diogenes Grigonio
# mesh operator

import bpy, bmesh, random, mathutils


class BASIC_OT_bmeshCreateVertical(bpy.types.Operator):
    """Create an object for each Vertical Face 
    using Matrices and applying Rotation Control 
    in Z Local Axis"""
    bl_idname = "basic.create_vertical"
    bl_label = "Create New"
    bl_options = {"REGISTER", "UNDO"}

    off_set = bpy.props.FloatProperty(
            name="Offset:",
            default=0.5)

    scale = bpy.props.FloatVectorProperty(
            name="Scale:",
            default=(1.0, 1.0, 1.0),
            size=3)

    rotate = bpy.props.FloatProperty(
            name="Rotate:",
            default=0.0,
            subtype='ANGLE', 
            unit='ROTATION')
            
    resolution = bpy.props.IntProperty(
            name="Resolution:",
            default=4,
            min=2, 
            max=24)

    point = bpy.props.EnumProperty(
            name="Origin:",
            items = (
            ("XZ", "XZ", ""),
            ("X-Z", "X-Z", ""),
            ("-XZ", "-XZ", ""),
            ("-X-Z", "-X-Z", ""),
            ("CENTER", "Center", ""),
            ("CENTERZ", "CenterZ", ""),
            ("CENTER-Z", "Center-Z", ""),
            ),
            default = "CENTER")

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob and ob.type == 'MESH' and context.mode == 'OBJECT'
    
    def execute(self, context):
        #variables
        FacePoint = self.point
        OffSet = self.off_set
        VertScale = self.scale
        Rotate = self.rotate
        VertMesh = []

        #BMesh Start
        BMesh = bmesh.new()
        BMesh.from_mesh(context.object.data)

        #Get Faces
        FaceToMesh = [f for f in BMesh.faces if len(f.verts)==4]

        #Loop over the Faces
        for Face in FaceToMesh:
            NormalX = Face.normal[0]
            NormalY = Face.normal[1]
            VertGroup = [vert.co for vert in Face.verts]
            MinZ = min([vert[2] for vert in VertGroup])
            SizeZ = max([vert[2] for vert in VertGroup]) - MinZ
            VertLow = [v for v in Face.verts if v.co[2]==MinZ]
            SizeSide = VertLow[1].co - VertLow[0].co
            VertXMax = VertLow[0].co[0]
            VertXMin = VertLow[1].co[0]
            
            if round(SizeSide[1], 3)>=0:
                VertYMax = min([VertLow[0].co[1], VertLow[1].co[1]])
                VertYMin = max([VertLow[0].co[1], VertLow[1].co[1]])
            else:
                VertYMax = max([VertLow[0].co[1], VertLow[1].co[1]])
                VertYMin = min([VertLow[0].co[1], VertLow[1].co[1]])

            VertZLow = VertLow[0].co[2]
            VertZUp = VertLow[0].co[2]+SizeZ
            
            #coordenadas para Point0 - 'Point0Co'
            if FacePoint == 'XZ':
                VertX = VertXMax+NormalX*OffSet
                VertY = VertYMax+NormalY*OffSet
                VertZ = VertZUp
            elif FacePoint == 'X-Z':
                VertX = VertXMax+NormalX*OffSet
                VertY = VertYMax+NormalY*OffSet
                VertZ = VertZLow
            elif FacePoint == '-XZ':
                VertX = VertXMin+NormalX*OffSet
                VertY = VertYMin+NormalY*OffSet
                VertZ = VertZUp
            elif FacePoint == '-X-Z':
                VertX = VertXMin+NormalX*OffSet
                VertY = VertYMin+NormalY*OffSet
                VertZ = VertZLow
            elif FacePoint == 'CENTER':
                VertX = (VertXMin-SizeSide[0]/2)+NormalX*OffSet
                VertY = (VertYMin-SizeSide[1]/2)+NormalY*OffSet
                VertZ = VertZLow+SizeZ/2
            elif FacePoint == 'CENTERZ':
                VertX = (VertXMin-SizeSide[0]/2)+NormalX*OffSet
                VertY = (VertYMin-SizeSide[1]/2)+NormalY*OffSet
                VertZ = VertZUp
            elif FacePoint == 'CENTER-Z':
                VertX = (VertXMin-SizeSide[0]/2)+NormalX*OffSet
                VertY = (VertYMin-SizeSide[1]/2)+NormalY*OffSet
                VertZ = VertZLow

            Point0Co = (VertX, VertY, VertZ)

            #Matrix Location
            MatrixLocation = mathutils.Matrix.Translation(Point0Co)

            #Matrix Scale
            MatrixScaleX = mathutils.Matrix.Scale(VertScale[0], 4, (1, 0, 0))
            MatrixScaleY = mathutils.Matrix.Scale(VertScale[1], 4, (0, 1, 0))
            MatrixScaleZ = mathutils.Matrix.Scale(VertScale[2], 4, (0, 0, 1))
            MatrixScale = MatrixScaleX*MatrixScaleY*MatrixScaleZ

            #Matrix Rotation
            RotationZ = mathutils.Euler((0, 0, Rotate), 'XYZ').to_quaternion()
            RotationZ = RotationZ.to_matrix().to_4x4()
            NormalOut = Face.normal
            FaceRot = NormalOut.to_track_quat('-Z', 'Y')
            FaceRot = FaceRot.to_matrix().to_4x4()
            MatrixRotation = FaceRot*RotationZ

            #Matrices
            Matrix = MatrixLocation*MatrixRotation*MatrixScale
            ObjectMatrix = context.object.matrix_basis

            #Create and Transform by Matrix
            ret = bmesh.ops.create_cone(
                                BMesh,
                                cap_ends=False,
                                cap_tris=True,
                                segments=self.resolution,
                                diameter1=0.01,
                                diameter2=0.7,
                                depth=0.5,
                                matrix=ObjectMatrix)

            bmesh.ops.transform(
                                BMesh, 
                                matrix=Matrix, 
                                space=ObjectMatrix, 
                                verts=ret['verts'])

            VertMesh.extend(ret['verts'])
            del ret

        #BMesh End
        BMesh.to_mesh(context.object.data)
        BMesh.free()
        context.object.data.update()

        return {"FINISHED"}
