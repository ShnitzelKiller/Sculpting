
from typing import List,Dict,Tuple

Vec3 = Tuple[float,float,float]
Mat3 = Tuple[Vec3,Vec3,Vec3]

class Solid:
    def __init__(self, iid, args):
        self.id = iid
        self.args = args

    def __repr__(self):
        return self.id

args_to_solid: Dict[str, Solid] = {}
create_order: List[Solid] = []


def GetSolid(*args) -> Solid:
    if args not in args_to_solid:
        next_id = "S"+str(len(args_to_solid))
        next_solid = Solid(next_id, args) 
        args_to_solid[args] = next_solid
        create_order.append(next_solid)
    return args_to_solid[args]



def Empty() -> Solid:
    return GetSolid("empty")

def Sphere() -> Solid:
    return GetSolid("sphere")

def Cube() -> Solid:
    return GetSolid("cube")

def Cone() -> Solid:
    return GetSolid("cone")


#todo: optimize multiple translate/transform in sequence
def Translate(s: Solid, by: Vec3) -> Solid:
    return GetSolid("translate", s, by)

def Transform(s: Solid, by: Mat3) -> Solid:
    return GetSolid("transform", s, by)

def Scale(s: Solid, by: Vec3) -> Solid:
    return Transform(s, ((by[0],0,0), (0,by[1],0), (0,0,by[2])))



def Union(*solids: Solid) -> Solid:
    return GetSolid("union", *solids)

def Intersect(*solids: Solid) -> Solid:
    return GetSolid("intersect", *solids)

def Subtract(a: Solid, b: Solid) -> Solid:
    return GetSolid("subtract", a, b)



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


def MarkUsed(used, s: Solid):
    if s not in used:
        used.add(s)
    for arg in s.args:
        if type(arg) is Solid:
            MarkUsed(used, arg)

