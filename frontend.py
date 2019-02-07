
class Vec3:
    def __init__(self, x, y, z):
        self.x=float(x)
        self.y=float(y)
        self.z=float(z)

class Mat3:
    def __init__(self, x, y, z):
        assert(type(x)==Vec3 and type(y)==Vec3 and type(z)==Vec3)
        self.x=x
        self.y=y
        self.z=z

class Transformation:
    def __init__(self,matrix,translation):
        assert(type(matrix) == Mat3 and type(translation) == Vec3)
        self.matrix = matrix
        self.translation = translation


class Solid:
    prefix = "S"
    def __init__(self, id_, discrete, args):
        self.id = id_
        self.args = args
        self.discrete = discrete

    def __repr__(self):
        return self.id

class Field:
    prefix = "F"
    def __init__(self, id_, discrete, args):
        self.id = id_
        self.args = args
        self.discrete = discrete

    def __repr__(self):
        return self.id

created_objects = {}
create_order = []

def GetObject(typ, ir, args):
    if typ not in (Solid, Field):
        raise Exception("invalid")
    if args not in created_objects:
        next_id = typ.prefix+str(len(created_objects))
        next_obj = typ(next_id, ir, args) 
        created_objects[args] = next_obj
        create_order.append(next_obj)
    return created_objects[args]

OperationRegistry = {}
def DoOperation(name, args):
    for func,argtypes in OperationRegistry[name]:
        if len(args) == len(argtypes):
            fixedargs = []
            for i in range(0,len(args)):
                if type(argtypes[i]) == tuple:
                    if type(args[i]) == argtypes[i][0]:
                        if argtypes[i][1] and not args[i].discrete:
                            fixedargs.append(Discretize(args[i]))
                        else:
                            fixedargs.append(args[i])
                    else:
                        break
                else:
                    if type(args[i]) == argtypes[i]:
                        fixedargs.append(args[i])
                    elif argtypes[i] == float:
                        fixedargs.append(float(args[i]))
                    else:
                        break
            else:
                return func(fixedargs)
    raise Exception("Invalid arguments: ", name, type(args), args)

def AddOperation(name, returntype, argtypes=[], body=False):
    def checktypearg(typearg):
        assert(type(typearg) in (type, tuple))
        if type(typearg) == type:
            assert(typearg not in (Solid, Field))
        else:
            assert(len(typearg) == 2)
            assert(typearg[0] in (Solid, Field))
            assert(type(typearg[1])==bool)
    assert(type(name) == str)
    assert(type(argtypes) == list)
    assert(type(returntype) == tuple)
    checktypearg(returntype)
    for arg in argtypes:
        checktypearg(arg)

    

    if body==False:
        def tempbody(args):
            return GetObject(returntype[0],returntype[1],(name,*args))
        body = tempbody

    assert(callable(body))

    if name not in OperationRegistry:
        OperationRegistry[name] = []

        def temp(*args):
            return DoOperation(name, args)

        globals()[name] = temp

    OperationRegistry[name].append( (body, argtypes) )

#works for either solid or field
#todo: optimize multiple translate/transform in sequence

for ObjType in (Solid, Field):
    AddOperation("Discretize", (ObjType, True), [(ObjType, False)])
    AddOperation("Transform", (ObjType, False), [(ObjType, False), Transformation])
    AddOperation("Translate", (ObjType, False), [(ObjType, False), Vec3], lambda args: Transform(args[0], Transformation(Mat3(Vec3(1,0,0),Vec3(0,1,0),Vec3(0,0,1)),args[1])) )
    AddOperation("Scale", (ObjType, False), [(ObjType, False), Vec3], lambda args: Transform(args[0], Transformation(Mat3(Vec3(args[1].x,0,0),Vec3(0,args[1].y,0),Vec3(0,0,args[1].z)),Vec3(0,0,0))) )


for primitive in ["Empty","Sphere","Cube","Cone","Cylinder"]:
    AddOperation(primitive, (Solid, False))

for setoperation in ["Union","Intersect","Subtract"]:
    AddOperation(setoperation, (Solid, False), [(Solid, False), (Solid, False)])

AddOperation("MoveSurface", (Solid, True), [(Solid, True), (Field, False), Vec3])

AddOperation("UniformField", (Field, False), [float])

AddOperation("SolidToField", (Field, False), [(Solid, False)])

AddOperation("BlurField", (Field, True), [(Field, True), float])

for fieldoperation in ["Add", "Subtract", "Multiply", "Max", "Min"]:
    AddOperation(fieldoperation, (Field, False), [(Field, False), (Field, False)])

AddOperation("Invert", (Field, False), [(Field, False)])


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
        if type(arg) in (Solid, Field):
            MarkUsed(used, arg)

