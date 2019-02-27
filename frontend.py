
import math
import sys

class Bounds:
    def __init__(self, x1, y1, x2=None, y2=None):
        if type(x1) == Vec2:
            self.lo = x1
            self.hi = y1
        else:
            self.lo = Vec2(x1, y1)
            self.hi = Vec2(x2, y2)
        if self.lo.x>=self.hi.x or self.lo.y>=self.hi.y: #empty
            self.lo=Vec2(0,0)
            self.hi=Vec2(0,0)

    def transformed(self, tf):
        corners = [tf.tf_vec(v) for v in (self.lo, Vec2(self.lo.x,self.hi.y), Vec2(self.hi.x,self.lo.y), self.hi)]
        return Bounds(Vec2.vmin(*corners), Vec2.vmax(*corners))

    def expanded(self, by):
        return Bounds(self.lo.x-by,self.lo.y-by,self.hi.x+by,self.hi.y+by)

    def merge(self, other):
        return Bounds(Vec2.vmin(self.lo,other.lo),Vec2.vmax(self.hi,other.hi))

    def intersect(self, other):
        return Bounds(Vec2.vmax(self.lo,other.lo),Vec2.vmin(self.hi,other.hi))

    def samples(self, resolution):
        return math.ceil((self.hi.x-self.lo.x)*resolution)*math.ceil((self.hi.y-self.lo.y)*resolution)

class Vec2:
    def __init__(self, x, y):
        self.x=float(x)
        self.y=float(y)

    def vmin(*args):
        return Vec2(min([v.x for v in args]),min([v.y for v in args]))

    def vmax(*args):
        return Vec2(max([v.x for v in args]),max([v.y for v in args]))

    def add(self, other):
        return Vec2(self.x+other.x, self.y+other.y)

    def mul(self, scalar):
        return Vec2(self.x*scalar, self.y*scalar)

    def dot(self, other):
        return self.x*other.x + self.y*other.y

    def magnitude(self):
        return math.sqrt(self.dot(self))

    def normalized(self):
        return self.mul(1.0/self.magnitude())

    def __repr__(self):
        return "(%.2f, %.2f)" % (self.x, self.y)

    def __eq__(self, other):
        return isinstance(other, Vec2) and self.__repr__()==other.__repr__()
    def __hash__(self):
        return hash(self.__repr__())

class Mat2x2:
    def __init__(self, xx, yx, xy, yy):
        self.xx=float(xx)
        self.yx=float(yx)
        self.xy=float(xy)
        self.yy=float(yy)
        self.scale_factor() #this will just check if it's degenerate

    def mul_vec(self, vec):
        return Vec2(self.xx*vec.x+self.xy*vec.y, self.yx*vec.x+self.yy*vec.y)

    def mul_mat(self, mat):
        return Mat2x2(self.xx*mat.xx + self.xy*mat.yx,
                        self.yx*mat.xx + self.yy*mat.yx,
                        self.xx*mat.xy + self.xy*mat.yy,
                        self.yx*mat.xy + self.yy*mat.yy)

    #if the matrix keeps proportions, it can still rotate or uniform scale and be square
    def is_square(self):
        tx = self.mul_vec(Vec2(1,0))
        ty = self.mul_vec(Vec2(0,1))
        #ty.magnitude() should not be zero or it is a degenerate matrix
        return abs((tx.magnitude()/ty.magnitude())-1.0) < 0.0001 and abs(tx.normalized().dot(ty.normalized())) < 0.0001

    #how much the matrix "blows up" the content in the strongest direction
    def scale_factor(self):
        #do svd https://scicomp.stackexchange.com/questions/8899/robust-algorithm-for-2-times-2-svd
        E = (self.xx+self.yy)*0.5
        F = (self.xx-self.yy)*0.5
        G = (self.yx+self.xy)*0.5
        H = (self.yx-self.xy)*0.5
        Q = math.sqrt(E*E + H*H)
        R = math.sqrt(F*F + G*G)
        assert abs(Q-R)>0.0000001, "Degenerate matrix"
        return max(Q+R, abs(Q-R))

    def __repr__(self):
        return "(%.2f, %.2f, %.2f, %.2f)" % (self.xx, self.yx, self.xy, self.yy)
    def __eq__(self, other):
        return isinstance(other, Mat2x2) and self.__repr__()==other.__repr__()
    def __hash__(self):
        return hash(self.__repr__())

class Transformation:
    def __init__(self,matrix,translation):
        assert(type(matrix) == Mat2x2 and type(translation) == Vec2)
        self.matrix = matrix
        self.translation = translation

    def post_transform(self, after):
        return Transformation(after.matrix.mul_mat(self.matrix), after.translation.add(after.matrix.mul_vec(self.translation)))

    def is_identity(self):
        return self.matrix.xx==1 and self.matrix.xy==0 and self.matrix.yx==0 and self.matrix.yy==1 and self.translation.x==0 and self.translation.y==0

    def tf_vec(self, vec):
        return self.translation.add(self.matrix.mul_vec(vec))

    def __repr__(self):
        return "(%r, %r)" % (self.matrix, self.translation)

    def __eq__(self, other):
        return isinstance(other, Transformation) and self.__repr__()==other.__repr__()
    def __hash__(self):
        return hash(self.__repr__())


IF_INPUTS_VALID = 3
#valid_if_inputs_valid_fn = lambda a: True if all([x.outputs_valid_sdf for x in a if type(x)==Solid]) else IF_INPUTS_VALID

class Node:
    def __init__(self, id_, fn, args, bounds, parent_samples_needed_fn, requires_valid_sdf, outputs_valid_sdf=True):
        self.id = id_
        self.fn = fn
        self.args = args
        self.input_nodes = []
        self.input_uncertain_sdf_solids = []
        for a in args:
            if type(a) in (Solid, Field):
                self.input_nodes.append(a)
                if type(a)==Solid and (a.outputs_valid_sdf is not True):
                    self.input_uncertain_sdf_solids.append(a)

        self.requires_valid_sdf = requires_valid_sdf

        if outputs_valid_sdf==IF_INPUTS_VALID and (requires_valid_sdf or len(self.input_uncertain_sdf_solids)==0):
            outputs_valid_sdf = True

        self.outputs_valid_sdf = outputs_valid_sdf

        self.output_nodes = []

        #what the resolution of the result of this node must be if discretized
        self.resolution = 0
        self.bounds = bounds

        self.parent_samples_needed = None
        self.parent_samples_needed_fn = parent_samples_needed_fn #wait until resolutions are computed for this

        self.sdf_flow_capacity = None

        self.discretize = False
        self.repair_sdf = False

    def __repr__(self):
        return self.id

    # def compute_parent_samples_needed(self):
    #     if self.parent_samples_needed is None:
    #         for n in self.input_nodes:
    #             n.compute_parent_samples_needed()
    #         self.parent_samples_needed = self.parent_samples_needed_fn(self)
            #self.sample_cost = 1
            #for inp in range(len(self.input_nodes)):
            #    self.sample_cost += self.parent_samples_needed[inp] * self.input_nodes[inp].sample_cost

    def DetourOutput(self, after):
        assert(self in after.args and self in after.input_nodes)
        after.output_nodes = self.output_nodes
        self.output_nodes = [after]
        for out in after.output_nodes:
            assert(self in out.args and self in out.input_nodes)
            out.args = tuple(after if a==self else a for a in out.args)
            out.input_nodes = [after if a==self else a for a in out.input_nodes]

class Solid(Node):
    prefix = "S"
    def __init__(self, id_, fn, args, bounds, parent_samples_needed_fn, requires_valid_sdf, outputs_valid_sdf, solid_outside_bounds):
        Node.__init__(self, id_, fn, args, bounds, parent_samples_needed_fn, requires_valid_sdf, outputs_valid_sdf=outputs_valid_sdf)
        self.solid_outside_bounds = solid_outside_bounds


class Field(Node):
    prefix = "F"
    def __init__(self, id_, fn, args, bounds, parent_samples_needed_fn, requires_valid_sdf, value_range, value_outside_bounds):
        Node.__init__(self, id_, fn, args, bounds, parent_samples_needed_fn, requires_valid_sdf)
        self.value_range = value_range
        self.value_outside_bounds = value_outside_bounds
        assert(value_outside_bounds>=value_range[0] and value_outside_bounds<=value_range[1])



created_objects = {}
create_order = []

def GetObject(typ, fn, args, cfs):
    args = tuple(args)
    if typ not in (Solid, Field):
        raise Exception("invalid")
    if (fn, args) not in created_objects:
        next_id = typ.prefix+str(len(created_objects))
        next_obj = typ(next_id, fn, args, **{k:(cfs.__dict__[k](args)) for k in cfs.__dict__})
        created_objects[(fn, args)] = next_obj
        create_order.append(next_obj)
    return created_objects[(fn, args)]

OperationRegistry = {}
def DoOperation(name, args):
    if name=="Transform":
        assert(type(args[0]) in (Solid, Field))
        if args[1].is_identity(): # skip no-op transforms
            return args[0]
        elif args[0].fn=="Transform": #combine sequential transforms
            prev = args[0]
            args = (prev.args[0], prev.args[1].post_transform(args[1]))
    for func,argtypes in OperationRegistry[name]:
        if len(args) == len(argtypes):
            fixedargs = []
            for i in range(0,len(args)):
                if type(args[i]) == argtypes[i]:
                    fixedargs.append(args[i])
                elif argtypes[i] == float:
                    fixedargs.append(float(args[i]))
                else:
                    break
            else:
                return func(fixedargs)
    raise Exception("Invalid arguments: ", name, type(args), args)


#class OperationData:
    #__init__(self, func,)

#  **a.__dict__

def check_wrap(val, check=True):
    if callable(val):
        return val
    else:
        assert(check)
        return lambda *args: val

class Obj(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def AddOperation(name, returntype, argtypes, bounds,
                requires_valid_sdf=None,
                outputs_valid_sdf=None, solid_outside_bounds=None,
                value_range=None, value_outside_bounds=None,
                parent_samples_needed_fn_fn=None):

    assert(type(name) == str)
    assert(returntype in (Solid, Field))
    assert(type(argtypes) == list)
    for arg in argtypes:
        assert(type(arg) == type)

    bounds = check_wrap(bounds, type(bounds)==Bounds)

    if parent_samples_needed_fn_fn==None:
        parent_samples_needed_fn_fn = lambda a: lambda n: [1 for arg in a if type(arg) in (Solid, Field)]
    assert(callable(parent_samples_needed_fn_fn))

    if Solid in argtypes:
        assert requires_valid_sdf is not None, "Need requires_valid_sdf for Solid inputs"
        requires_valid_sdf=check_wrap(requires_valid_sdf, type(requires_valid_sdf)==bool)
    else:
        assert requires_valid_sdf is None, "requires_valid_sdf not used"
        requires_valid_sdf=check_wrap(False)

    if returntype==Solid:
        outputs_valid_sdf = check_wrap(outputs_valid_sdf, type(outputs_valid_sdf) is bool or outputs_valid_sdf==IF_INPUTS_VALID)
        solid_outside_bounds = check_wrap(solid_outside_bounds, type(solid_outside_bounds) is bool)
        assert value_range is None, "Unused for Solid output"
        assert value_outside_bounds is None, "Unused for Solid output"
    else:
        assert outputs_valid_sdf is None, "Unused for Field output"
        assert solid_outside_bounds is None, "Unused for Field output"
        value_range = check_wrap(value_range, type(value_range)==tuple and len(value_range)==2 and type(value_range[0]) in (float,int) and type(value_range[1]) in (float,int))
        value_outside_bounds = check_wrap(value_outside_bounds, type(value_outside_bounds) in (float,int))
      
    if name not in OperationRegistry:
        OperationRegistry[name] = []
        globals()[name] = lambda *args: DoOperation(name, args)

    if returntype==Solid:
        construction_funcs = Obj(bounds=bounds, requires_valid_sdf=requires_valid_sdf, parent_samples_needed_fn=parent_samples_needed_fn_fn,
                                    outputs_valid_sdf=outputs_valid_sdf, solid_outside_bounds=solid_outside_bounds)
    else:
        construction_funcs = Obj(bounds=bounds, requires_valid_sdf=requires_valid_sdf, parent_samples_needed_fn=parent_samples_needed_fn_fn,
                                    value_range=value_range, value_outside_bounds=value_outside_bounds)

    OperationRegistry[name].append( ((lambda args: GetObject(returntype, name, args, construction_funcs)), argtypes) )

#AddOperation("Discretize", (ObjType, True), [(ObjType, False)])

def Translate(obj, vec):
    return Transform(obj, Transformation(Mat2x2(1,0,0,1),vec))

def Scale(obj, vec):
    return Transform(obj, Transformation(Mat2x2(vec.x,0,0,vec.y),Vec2(0,0)))

def Rotate(obj, ang):
    return Transform(obj, Transformation(Mat2x2(math.cos(math.radians(ang)),math.sin(math.radians(ang)),-math.sin(math.radians(ang)),math.cos(math.radians(ang))),Vec2(0,0)))

def Subtract(a, b):
    assert(type(a) == Solid and type(b) == Solid)
    return Intersect2(a, Invert(b))

def Intersect2(a, b):
    return Invert(Union2(Invert(a), Invert(b)))

#makes functions that can use arbitrary number of args
for expand2 in ("Union","Intersect","Add","Multiply","Max","Min"):
    def temp2(expand):
        def temp(*args):
            itm = args[0]
            for i in range(1,len(args)):
                itm = globals()[expand+"2"](itm, args[i])
            return itm
        globals()[expand] = temp
    temp2(expand2) #fixes dumb scope stuff

AddOperation("Transform", Solid, [Solid, Transformation],
    bounds=lambda a: a[0].bounds.transformed(a[1]),
    requires_valid_sdf=False,
    outputs_valid_sdf=lambda a: a[1].matrix.is_square(),
    solid_outside_bounds=lambda a: a[0].solid_outside_bounds)

AddOperation("Transform", Field, [Field, Transformation],
    bounds=lambda a: a[0].bounds.transformed(a[1]),
    value_range=lambda a: a[0].value_range,
    value_outside_bounds=lambda a: a[0].value_outside_bounds)

AddOperation("Circle", Solid, [],
    bounds=Bounds(-1,-1,1,1),
    outputs_valid_sdf=True,
    solid_outside_bounds=False)

AddOperation("Square", Solid, [],
    bounds=Bounds(-1,-1,1,1),
    outputs_valid_sdf=True,
    solid_outside_bounds=False)

AddOperation("UniformSolid", Solid, [bool],
    bounds=Bounds(0,0,0,0),
    outputs_valid_sdf=True,
    solid_outside_bounds=lambda a: a[0])

AddOperation("Union2", Solid, [Solid, Solid],
    bounds=lambda a: ( ( a[0].bounds.intersect(a[1].bounds) ) if a[1].solid_outside_bounds else ( a[1].bounds ) ) if a[0].solid_outside_bounds else ( ( a[0].bounds ) if a[1].solid_outside_bounds else ( a[0].bounds.merge(a[1].bounds) ) ),
    requires_valid_sdf=False,
    outputs_valid_sdf=IF_INPUTS_VALID,
    solid_outside_bounds=lambda a: a[0].solid_outside_bounds or a[1].solid_outside_bounds )

AddOperation("Invert", Solid, [Solid],
    bounds=lambda a: a[0].bounds,
    requires_valid_sdf=False,
    outputs_valid_sdf=IF_INPUTS_VALID,
    solid_outside_bounds=lambda a: not a[0].solid_outside_bounds )

AddOperation("ExpandSurface", Solid, [Solid, Field, float], 
    bounds=lambda a: a[0].bounds.expanded(max(a[2]*a[1].value_range[0], a[2]*a[1].value_range[1])),
    requires_valid_sdf=True,
    outputs_valid_sdf=False,
    solid_outside_bounds=lambda a: a[0].solid_outside_bounds)

AddOperation("UniformField", Field, [float],
    bounds=Bounds(0,0,0,0),
    value_range=lambda a: (a[0],a[0]),
    value_outside_bounds=lambda a: a[0])

AddOperation("SolidToField", Field, [Solid],
    bounds=lambda a: a[0].bounds,
    requires_valid_sdf=False,
    value_range=(0,1),
    value_outside_bounds=lambda a: 1 if a[0].solid_outside_bounds else 0)

#arg is standard deviation, do 3 std
AddOperation("BlurFieldX", Field, [Field, float],
    bounds=lambda a: a[0].bounds.expanded(abs(a[1])*3.0),
    value_range=lambda a: a[0].value_range,
    value_outside_bounds=lambda a: a[0].value_outside_bounds,
    parent_samples_needed_fn_fn=lambda a: lambda n: [math.ceil(n.resolution*a[1]*6)])

AddOperation("BlurFieldY", Field, [Field, float],
    bounds=lambda a: a[0].bounds.expanded(abs(a[1])*3.0),
    value_range=lambda a: a[0].value_range,
    value_outside_bounds=lambda a: a[0].value_outside_bounds,
    parent_samples_needed_fn_fn=lambda a: lambda n: [math.ceil(n.resolution*a[1]*6)])

def BlurField(field, std):
    return BlurFieldY(BlurFieldX(field, std), std)

# AddOperation("Add2", Field, [Field, Field])
# AddOperation("Multiply2", Field, [Field, Field])
# AddOperation("Max2", Field, [Field, Field])
# AddOperation("Min2", Field, [Field, Field])

# AddOperation("Invert", Field, [Field])

AddOperation("OutputNode", Solid, [Solid], 
    bounds=lambda a: a[0].bounds,
    requires_valid_sdf=True,
    outputs_valid_sdf=True,
    solid_outside_bounds=lambda a: a[0].solid_outside_bounds)

#while iterating you can change the outputs of the visiting node and any unvisited nodes, but not anything thats been visited already
def creation_order(graph_top):
    fringe = graph_top.copy()
    inputs_visited = {}
    outputs_visited = {}
    while len(fringe)>0:
        next = fringe.pop(0)
        outputs_visited[next] = 0
        used_inputs = []
        for inp in next.input_nodes:
            outputs_visited[inp] += 1
            if outputs_visited[inp]>=len(inp.output_nodes):
                assert(outputs_visited[inp]==len(inp.output_nodes))
                used_inputs.append(inp)
        yield (next, used_inputs)
        for out in next.output_nodes:
            if out not in inputs_visited:
                inputs_visited[out] = 0
            inputs_visited[out] += 1
            if inputs_visited[out]>=len(out.input_nodes):
                assert(inputs_visited[out]==len(out.input_nodes))
                fringe.append(out)


has_run_output = False

#this should only be run one time because it edits the nodes
def Output(final, resolution=100):
    global has_run_output
    assert not has_run_output
    has_run_output = True

    assert type(final)==Solid
    assert not final.solid_outside_bounds
    output_final = OutputNode(final)

    graph_top = []

    #fills in node outputs while pruning unused paths
    def find_outputs(s):
        has_input = False
        for arg in s.args:
            if type(arg) in (Solid, Field):
                has_input = True
                if len(arg.output_nodes)==0: #hasn't been visited yet
                    find_outputs(arg)
                arg.output_nodes.append(s)
        if not has_input and s not in graph_top:
            graph_top.append(s)

    find_outputs(output_final)

    # traverse upward to figure out the resolution of each node
    output_final.resolution = resolution
    fringe = [output_final]
    resolutions_measured = {}
    while len(fringe)>0:
        next = fringe.pop(0)
        #if next.fn=="Transform" and next.args[1].matrix.scale_factor()>1:
            #print(next)
        input_res = next.resolution*next.args[1].matrix.scale_factor() if next.fn=="Transform" else next.resolution
        for inp in next.input_nodes:
            inp.resolution = max(inp.resolution, input_res)
            if inp not in resolutions_measured:
                resolutions_measured[inp]=0
            resolutions_measured[inp]+=1
            if resolutions_measured[inp]==len(inp.output_nodes):
                fringe.append(inp)

    #creation_order is now valid

    invalid_sdf_entries = []
    sdf_cut = set()
    for n,dl in creation_order(graph_top):
        if n.outputs_valid_sdf == False:
            invalid_sdf_entries.append(n)

    def SearchSDFGraph():
        for n in invalid_sdf_entries:
            succ, path = RecurseSDFGraph(n)
            if succ:
                return True, path
        return False, None

    def RecurseSDFGraph(n1):
        if n1.sdf_flow_capacity is None:
            n1.sdf_flow_capacity = n1.bounds.samples(n1.resolution)
        if n1.sdf_flow_capacity<=0:
            assert(n1.sdf_flow_capacity==0)
            sdf_cut.add(n1)
            return False, None
        for n2 in n1.output_nodes:
            #found the bottom
            if n2.requires_valid_sdf:
                return True, [n1]
            #if it's T or F ignore it
            if n2.outputs_valid_sdf==IF_INPUTS_VALID:
                succ, path = RecurseSDFGraph(n2)
                if succ:
                    path.append(n1)
                    return True, path
        return False, None

    while True:
        succ, path = SearchSDFGraph()
        if not succ:
            break
        limit = min([n.sdf_flow_capacity for n in path])
        assert(limit>0)
        for n in path:
            n.sdf_flow_capacity-=limit

    for fixme in sdf_cut:
        fixme.discretize = True
        fixme.repair_sdf = True

    #input_uncertain_sdf_nodes and other sdf stuff is no longer valid or needed

    #discretize output of any node with more than 1 output or is sampled more than once (todo use dynamic programming or something to make this better?)
    for n,dl in creation_order(graph_top):
        n.parent_samples_needed = n.parent_samples_needed_fn(n)

    for n,dl in creation_order(graph_top):
        if sum(o.parent_samples_needed[o.input_nodes.index(n)] for o in n.output_nodes) > 1:
            n.discretize = True

    final.discretize=True

    command_list = []

    for n,delete in creation_order(graph_top):
        #bounds = " {%.2f,%.2f,%.2f,%.2f}*%.2f" % (n.bounds.lo.x, n.bounds.lo.y, n.bounds.hi.x, n.bounds.hi.y, n.resolution)
        #print(n.id + bounds + " =", n.fn, n.args))
        if n.fn == "OutputNode":
            #print("\n".join([repr(c) for c in command_list]))
            return command_list

        cmd = {"cmd":"create",
                "type":"solid" if type(n) == Solid else "field",
                "id":n.id,
                "fn": n.fn,
                "args": tuple([a if type(a) not in (Solid, Field) else a.id for a in n.args])}

        if type(n) == Solid:
            cmd["oob_solid"] = n.solid_outside_bounds

        if type(n) == Field:
            cmd["oob_value"] = n.value_outside_bounds

        if n.discretize:
            cmd["discretize"] = { "bbox":[n.bounds.lo.x, n.bounds.lo.y, n.bounds.hi.x, n.bounds.hi.y], "resolution":n.resolution, "repair_sdf":n.repair_sdf }

        command_list.append(cmd)

        #TODO: define internal commands for mutable input/output; reuse buffers when possible
        #NOTE: will delete objects low in a tree while the root is in use, so don't actually free them until tree is freed (discretized) (TODO change?)
        for d in delete:
            if d.discretize:
                command_list.append( {"cmd":"delete","id":d.id})
    
    assert False, "didn't find end of list!"




