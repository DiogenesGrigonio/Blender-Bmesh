import bpy, bmesh, random

context = bpy.context


def popup_message(message, title="Erro", icon='ERROR'):
    def oops(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(oops, title=title, icon=icon)


def create_face(BMesh, Edge, Vector):
    ret = bmesh.ops.extrude_edge_only(
                BMesh,
                edges=[Edge])
    E1 = [ele for ele in ret["geom"]
            if isinstance(ele, bmesh.types.BMEdge)]
    del ret
    for v in E1[0].verts:
        bmesh.ops.translate(
                BMesh,
                verts=[v],
                vec=Vector)
    return E1


def unselect_all(BMesh):
    BMesh.select_mode = {'VERT', 'EDGE', 'FACE'}
    for v in BMesh.verts:v.select_set(False)
    BMesh.select_flush_mode()


def select_el(BMesh, List):
    for el in List:el.select_set(True)
    BMesh.select_flush(True)


def convert_list(BMesh, InGroup, TypeIn, TypeOut):
    unselect_all(BMesh)
    if TypeIn=='Vert' and TypeOut=='Edge':
        select_el(BMesh, InGroup)
        OutGroup = [e for e in BMesh.edges if e.select] 
    elif TypeIn=='Vert' and TypeOut=='Face':
        select_el(BMesh, InGroup)
        OutGroup = [f for f in BMesh.faces if f.select]
    elif TypeIn=='Edge' and TypeOut=='Vert':
        OutGroup = []
        for item in [v for e in BMesh.edges 
                    if e in InGroup 
                    for v in e.verts]:
            if item not in OutGroup:OutGroup.append(item)
    elif TypeIn=='Edge' and TypeOut=='Face':
        select_el(BMesh, InGroup)
        OutGroup = [f for f in BMesh.faces if f.select]
    elif TypeIn=='Face' and TypeOut=='Vert':
        OutGroup = list({v for f in InGroup for v in f.verts})
    elif TypeIn=='Face' and TypeOut=='Edge':
        select_el(BMesh, InGroup)
        OutGroup = [e for e in BMesh.edges if e.select]
    unselect_all(BMesh)
    return OutGroup


def curtains(BMesh, FacesIn, CurtainType, CurtainResol, Seed):
    FaceToCurtains = [f for f in FacesIn if len(f.verts)==4]
    Thick = 0.03
    EdgeCurtain=[]

    #create Curtains 
    for Face in FaceToCurtains:
        NormalX = Face.normal[0]
        NormalY = Face.normal[1]
        VertGroup = [vert.co for vert in Face.verts]
        MinZ = min([vert[2] for vert in VertGroup])
        SizeZ = max([vert[2] for vert in VertGroup]) - MinZ
        VertLow = [v for v in Face.verts if v.co[2]==MinZ]

        if len(VertLow)!=2:
            popup_message("Janela com desnível na base")
            continue

        SizeSide = VertLow[1].co - VertLow[0].co

        #coordenadas para Vert 0
        VertX = VertLow[0].co[0]
        if round(SizeSide[1], 3)>=0:
            VertY = min([VertLow[0].co[1], VertLow[1].co[1]])
        else:
            VertY = max([VertLow[0].co[1], VertLow[1].co[1]])

        #"""Curtain A"""
        if CurtainType==1:
            LocalZ =  -SizeZ/CurtainResol
            
            #coordenadas para Vert 0 - 'Vert0Co'
            VertZ = VertLow[0].co[2]+SizeZ
            Vert0Co = [VertX-NormalX*0.02, VertY-NormalY*0.02, VertZ]

            #Vert 0
            v = bmesh.ops.create_vert(BMesh,co=Vert0Co)
            V0 = v['vert'][0]
            
            #Edge 0
            ret = bmesh.ops.extrude_vert_indiv(
                        BMesh,
                        verts=[V0])
            bmesh.ops.translate(
                        BMesh,
                        verts=[V0],
                        vec=SizeSide)
            E1=[ret['edges'][0]]
            EdgeCurtain.extend(E1)
            del v, ret, E1

            #Faces
            random.seed(Seed+Face.index)
            RangeCurtain = 1+int(SizeZ*CurtainResol*random.uniform(-0.2,1.1)/4)
            for i in range(RangeCurtain):
                #face1
                E1 = create_face(BMesh, 
                                EdgeCurtain[-1], 
                                (0,0,LocalZ))
                EdgeCurtain.extend(E1)
                #face2
                E1 = create_face(BMesh, 
                                EdgeCurtain[-1], 
                                (-NormalX*Thick,-NormalY*Thick,0))
                EdgeCurtain.extend(E1)
                #face3
                E1 = create_face(BMesh, 
                                EdgeCurtain[-1], 
                                (0,0,LocalZ))
                EdgeCurtain.extend(E1)
                #face4
                E1 = create_face(BMesh, 
                                EdgeCurtain[-1], 
                                (NormalX*Thick,NormalY*Thick,0))
                EdgeCurtain.extend(E1)

        #"""Curtain B"""
        elif CurtainType==2:
            EdgeLocal = []
                            
            #coordenadas para Vert 0 - 'Vert0Co'
            VertZ = VertLow[0].co[2]-0.01
            Vert0Co = [VertX, VertY, VertZ]

            #Folha L
            EdgeLocal = []
            v = bmesh.ops.create_vert(BMesh,co=Vert0Co)
            V0 = v['vert'][0]
            ret = bmesh.ops.extrude_vert_indiv(
                        BMesh,
                        verts=[V0])
            bmesh.ops.translate(
                        BMesh,
                        verts=[V0],
                        vec=(0, 0, SizeZ+0.02))
            E1=[ret['edges'][0]]
            EdgeCurtain.extend(E1)
            for v in E1[0].verts:
                bmesh.ops.translate(
                        BMesh,
                        verts=[v],
                        vec=(-NormalX*0.115, -NormalY*0.115, 0))
            del v, ret, E1
            for i in range(int(CurtainResol/random.uniform(2,8))):
                E1 = create_face(BMesh, EdgeCurtain[-1], 
                    (   SizeSide[0]/CurtainResol,
                        SizeSide[1]/CurtainResol,
                        0))
                EdgeCurtain.extend(E1)
                EdgeLocal.extend(E1)
            for e in EdgeLocal:
                for v in e.verts:
                    v.co = (v.co[0]+NormalX*random.uniform(0.105,0),
                            v.co[1]+NormalY*random.uniform(0.105,0),
                            v.co[2])
            del EdgeLocal

            #Folha R
            EdgeLocal = []
            Vert1Co = [VertX+SizeSide[0], VertY+SizeSide[1], VertZ]
            v = bmesh.ops.create_vert(BMesh,co=Vert1Co)
            V1 = v['vert'][0]
            ret = bmesh.ops.extrude_vert_indiv(
                        BMesh,
                        verts=[V1])
            bmesh.ops.translate(
                        BMesh,
                        verts=[V1],
                        vec=(0, 0, SizeZ+0.02))
            E1=[ret['edges'][0]]
            EdgeCurtain.extend(E1)
            EdgeLocal.extend(E1)
            for v in E1[0].verts:
                bmesh.ops.translate(
                        BMesh,
                        verts=[v],
                        vec=(-NormalX*0.115, -NormalY*0.115, 0))
            del v, ret, E1
            for i in range(int(CurtainResol/random.uniform(2,8))):
                E1 = create_face(BMesh, EdgeCurtain[-1], 
                    (   -SizeSide[0]/CurtainResol,
                        -SizeSide[1]/CurtainResol,
                        0))
                EdgeCurtain.extend(E1)
                EdgeLocal.extend(E1)
            for e in EdgeLocal[1:]:
                for v in e.verts:
                    v.co = (v.co[0]+NormalX*random.uniform(0.105,0),
                            v.co[1]+NormalY*random.uniform(0.105,0),
                            v.co[2])
            del EdgeLocal

    FaceCurtain = convert_list(BMesh, EdgeCurtain, 'Edge', 'Face')
    if CurtainType==2:
        for face in FaceCurtain:face.smooth = True


    return FaceCurtain
