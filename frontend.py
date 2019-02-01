
from typing import List,Dict,Tuple

Vec3 = Tuple[float,float,float]
Mat3 = Tuple[Vec3,Vec3,Vec3]
Transformation = Tuple[Mat3, Vec3]

class Flyweight:
    def __init__(self, id_, args):
        self.id = id_
        self.args = args

    def __repr__(self):
        return self.id

class Solid(Flyweight):
    prefix = "S"
    def __init__(self, *args):
        Flyweight.__init__(self, *args)

class Field(Flyweight):
    prefix = "F"
    def __init__(self, *args):
        Flyweight.__init__(self, *args)

created_objects = {}
create_order = []

def GetObj(typ, *args):
    if typ not in (Solid, Field):
        raise Exception("invalid")
    if args not in created_objects:
        next_id = typ.prefix+str(len(created_objects))
        next_solid = typ(next_id, args) 
        created_objects[args] = next_solid
        create_order.append(next_solid)
    return created_objects[args]



#python type checking is NOT actually enforced, TODO make function generator that checks types

#works for either solid or field
#todo: optimize multiple translate/transform in sequence
def Transform(s, by: Transformation):
    return GetObj(type(s), "transform", s, by)

def Translate(s, by: Vec3):
    return Transform(s, ( ((1,0,0), (0,1,0), (0,0,1)), by ) )

def Scale(s, by: Vec3):
    return Transform(s, ( ((by[0],0,0), (0,by[1],0), (0,0,by[2])), (0,0,0) ) )



def Empty() -> Solid:
    return GetObj(Solid, "empty")

def Sphere() -> Solid:
    return GetObj(Solid, "sphere")

def Cube() -> Solid:
    return GetObj(Solid, "cube")

def Cone() -> Solid:
    return GetObj(Solid, "cone")

def Cylinder() -> Solid:
    return GetObj(Solid, "cylinder")


def Union(*solids: Solid) -> Solid:
    return GetObj(Solid, "union", *solids)

def Intersect(*solids: Solid) -> Solid:
    return GetObj(Solid, "intersect", *solids)

def Subtract(a: Solid, b: Solid) -> Solid:
    return GetObj(Solid, "subtract", a, b)

def MoveSurface(s: Solid, mask: Field, by: Vec3) -> Solid:
    return GetObj(Solid, "movesurface", s, mask)


def UniformField(v: float) -> Field:
    return GetObj(Field, "uniform", v)

def SolidToField(a: Solid) -> Field:
    return GetObj(Field, "fromsolid", a)


def BlurField(a: Field, by: float) -> Field:
    return GetObj(Field, "blur", a, by)

def Add(a: Field, b: Field) -> Field:
    return GetObj(Field, "add", a, b)

def Sub(a: Field, b: Field) -> Field:
    return GetObj(Field, "sub", a, b)

def Mul(a: Field, b: Field) -> Field:
    return GetObj(Field, "mul", a, b)

def Max(a: Field, b: Field) -> Field:
    return GetObj(Field, "max", a, b)

def Min(a: Field, b: Field) -> Field:
    return GetObj(Field, "min", a, b)

def Invert(a: Field) -> Field:
    return Sub(UniformField(1), a)


def Output(final: Solid):
    used = set()
    MarkUsed(used, final)

    final_order = []
    for s in create_order:
        if s in used:
            final_order.append( (s, []) )

    for i in range(len(final_order)-1): #first thru second to last
        for j in range(len(final_order)-1, i, -1): #last thru one after i
            if final_order[i][0] in final_order[j][0].args:
                final_order[j][1].append(final_order[i][0]) #figure out when we can delete stuff
                break
        else:
            assert(False)

    for s in final_order:

        print(s[0].id, s[0].args)

        #todo: define internal commands for mutable input/output; reuse buffers when possible
        for d in s[1]:
            print("del "+d.id)
    
    print("Output "+final.id)


def MarkUsed(used, s):
    if s not in used:
        used.add(s)
    for arg in s.args:
        if issubclass(type(arg), Flyweight):
            MarkUsed(used, arg)

