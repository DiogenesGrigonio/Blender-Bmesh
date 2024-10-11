# GPL # (c) 2024 Diogenes Grigonio
# mesh operator

import bpy, bmesh, random, math


class BASIC_OT_bmeshRainDirt(bpy.types.Operator):
    """Create an object for use in Dirt Calculation"""
    bl_idname = "basic.rain_dirt"
    bl_label = "Rain Dirt"
    bl_options = {"REGISTER", "UNDO"}

    height = bpy.props.FloatProperty(
            name="Height",
            default=0.25,
            min=0.01)

    cuts = bpy.props.IntProperty(
            name="Cuts",
            default=50,
            min=1)

    amount = bpy.props.IntProperty(
            name="Amount",
            default=50,
            min=10,
            max=100,
            subtype='PERCENTAGE')

    distance = bpy.props.FloatProperty(
            name="Distance",
            default=1.9,
            min=0.0)

    height = bpy.props.FloatProperty(
            name="Height",
            default=0.25,
            min=0.01)

    invert_distance = bpy.props.BoolProperty(
            name="Invert",
            default=False)

    invert = bpy.props.BoolProperty(
            name="Invert Drops",
            default=False)

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob and ob.type == 'MESH' and context.mode == 'OBJECT'

    def execute(self, context):
        #BMesh Start
        BMesh = bmesh.new()
        BMesh.from_mesh(context.object.data)
        
        #Variables
        Cuts = self.cuts
        Amount = 1 - (self.amount/100)
        InvertDistance = -1 if self.invert_distance else 1
        Distance = self.distance * InvertDistance
        Height = self.height
        Invert = -1 if self.invert else 1

        #Subdivide selected Edges
        EdgesToSubdivide = [edge for edge in BMesh.edges if edge.select]

        bmesh.ops.split_edges(
            BMesh, 
            edges=EdgesToSubdivide)

        EdgeSubdivided = bmesh.ops.subdivide_edges(
                BMesh,
                edges=EdgesToSubdivide,
                cuts=Cuts)

        #Create Original Verts List - 'VertsOriginal'
        SubVert = [ele for ele in EdgeSubdivided["geom_split"]
                           if isinstance(ele, bmesh.types.BMVert)]                   
        VertsOriginal = [v for v in BMesh.verts if v not in SubVert]

        #Create 'EdgesSelected' and 'VertsSubdiv'
        EdgesSelect = [ele for ele in EdgeSubdivided["geom"]
                           if isinstance(ele, bmesh.types.BMEdge)]  
        VertsSubdiv = list({v for e in EdgesSelect for v in e.verts})

        #Extrude New Edges
        ExtrudeEdgeOnly = bmesh.ops.extrude_edge_only(    
                BMesh,
                edges=EdgesSelect,
                use_select_history=True)

        #Translate vertices in 'VertsSubdiv'
        for Vert in VertsSubdiv:
            bmesh.ops.translate(
                    BMesh,
                    verts=[Vert],
                    vec=(0, 0, -0.02))

        for Vert in VertsSubdiv:
            bmesh.ops.translate(
                    BMesh,
                    verts=[Vert],
                    vec=(   Vert.normal[0]/12*Distance, 
                            Vert.normal[1]/12*Distance, 
                            0))

        #Get Faces and Flip (if necessary)
        Faces = [ele for ele in ExtrudeEdgeOnly["geom"]
                           if isinstance(ele, bmesh.types.BMFace)]
        if self.invert_distance:
            bmesh.ops.reverse_faces(
                        BMesh, 
                        faces=Faces)

        #Get Edges List - 'EdgesToExtrude',  from Vert List - 'VertsSubdiv'
        for v in VertsSubdiv:v.select = True
        BMesh.select_flush_mode()
        EdgesToExtrude = [e for e in BMesh.edges if e.select]
        for e in BMesh.edges:e.select = False
        BMesh.select_flush_mode()

        #Get random Edges
        NonExtrudeEdges = []
        for i in range(int(len(EdgesToExtrude)*Amount)):
            RandomElement = random.choice(EdgesToExtrude)
            NonExtrudeEdges.append(RandomElement)
            del EdgesToExtrude[EdgesToExtrude.index(RandomElement)]

        #Dissolve Vertices
        VertsOn = list({v for e in BMesh.edges 
                        if e in EdgesSelect 
                        for v in e.verts})
        VertsOff = list({v for e in BMesh.edges 
                        if e in EdgesToExtrude 
                        for v in e.verts})
        Verts = [v for v in VertsOn 
                if v not in VertsOff 
                and v not in VertsOriginal]
        bmesh.ops.dissolve_verts(BMesh, verts=Verts)

        #Extrude Edges
        ExtrudedEdges = bmesh.ops.extrude_edge_only(    
                BMesh,
                edges=EdgesToExtrude,
                use_select_history=True)
                
        #Get list 'EdgesSelected' from 'ExtrudedEdges'
        EdgesSelected = [ele for ele in ExtrudedEdges["geom"]
                           if isinstance(ele, bmesh.types.BMEdge)]

        #Get Verts from extruded Edges
        VertsSelect = [ele for ele in ExtrudedEdges["geom"]
                           if isinstance(ele, bmesh.types.BMVert)]

        #Translate all extruded Verts
        bmesh.ops.translate(
                BMesh,
                verts=VertsSelect,
                vec=(0.0, 0.0, -0.02))

        #Split Edges
        for v in VertsSelect:
            if len(v.link_edges)==3:
                bmesh.ops.split_edges(
                    BMesh, 
                    edges=[v.link_edges[2]])

        #Translate only odd extruded Verts
        for Edge in EdgesSelected:
            EdgeHeight = Height*-random.random()
            RandomLoc = random.random()
            for Vert in Edge.verts:
                NormalX = (Vert.normal[0]/10)*RandomLoc*Invert
                NormalY = (Vert.normal[1]/10)*RandomLoc*Invert
                bmesh.ops.translate(
                        BMesh,
                        verts=[Vert],
                        vec=(NormalX, NormalY, EdgeHeight))

        #BMesh End
        BMesh.to_mesh(context.object.data)
        BMesh.free()
        context.object.data.update()

        #Apply SubSurface Modifier
        if 'SubSurf' not in context.object.modifiers:
            context.object.modifiers.new('SubSurf', 'SUBSURF')
            context.object.modifiers['SubSurf'].levels=1
            context.object.modifiers['SubSurf'].render_levels=3

        #Apply Smooth
        context.object.data.use_auto_smooth
        context.object.data.auto_smooth_angle = math.radians(60)
        bpy.ops.object.shade_smooth()

        return {"FINISHED"}