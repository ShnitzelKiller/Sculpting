
import math
import sys

class Bounds:
    def __init__(self, x1, y1, x2, y2):
        if type(x1) == Vec2:
            self.lo = x1
            self.hi = y1
        else:
            self.lo = Vec2(x1, y1)
            self.hi = Vec2(x2, y2)

    def transformed(self, tf):
        corners = [tf.tf_vec(v) for v in (self.lo, Vec2(self.lo.x,self.hi.y), Vec2(self.hi.x,self.lo.y), self.hi)]
        return BBox(Vec2.vmin(*corners), Vec2.vmax(*corners))

    def merge(self, other):
        return Bounds(Vec2.vmin(self.lo,other.lo),Vec2.vmax(self.hi,other.hi))

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
        return "(%r, %r)" % (self.x, self.y)

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
        return "(%r, %r, %r, %r)" % (self.xx, self.yx, self.xy, self.yy)
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

class Node:
    def __init__(self, id_, fn, args, bounds, sample_cost_fn, requires_valid_sdf, outputs_valid_sdf=True):
        self.id = id_
        self.fn = fn
        self.args = args
        self.input_nodes = []
        self.input_uncertain_solids = []
        for a in args:
            if type(a) in (Solid, Field):
                self.input_nodes.append(a)
                if type(a)==Solid and (a.outputs_valid_sdf is not True):
                    self.input_uncertain_solids.append(a)

        self.requires_valid_sdf = requires_valid_sdf

        if outputs_valid_sdf==IF_INPUTS_VALID and (requires_valid_sdf or len(self.input_uncertain_solids)==0):
            outputs_valid_sdf = True

        self.outputs_valid_sdf = outputs_valid_sdf

        self.output_nodes = []

        #what the resolution of the result of this node must be if discretized
        self.resolution = 0
        self.bounds = bounds

    def __repr__(self):
        return self.id


class Solid(Node):
    prefix = "S"
    def __init__(self, id_, fn, args, bounds, sample_cost_fn, requires_valid_sdf, outputs_valid_sdf, solid_outside_bounds):
        Node.__init__(self, id_, fn, args, bounds, sample_cost_fn, requires_valid_sdf, outputs_valid_sdf=outputs_valid_sdf)
        self.solid_outside_bounds = solid_outside_bounds


class Field(Node):
    prefix = "F"
    def __init__(self, id_, fn, args, bounds, sample_cost_fn, requires_valid_sdf, value_outside_bounds):
        Node.__init__(self, id_, fn, args, bounds, sample_cost_fn, requires_valid_sdf)
        self.value_outside_bounds = value_outside_bounds



created_objects = {}
create_order = []

def GetObject(typ, fn, args, cfs):
    args = tuple(args)
    if typ not in (Solid, Field):
        raise Exception("invalid")
    if args not in created_objects:
        next_id = typ.prefix+str(len(created_objects))

        next_obj = typ(next_id, fn, args, **{k:(cfs.__dict__[k](args)) for k in cfs.__dict__})

        created_objects[args] = next_obj
        create_order.append(next_obj)
    return created_objects[args]

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

def wrap(val):
    return lambda *args: val

class Obj(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def AddOperation(name, returntype, argtypes, bounds="TEMP" ,
                                    sample_cost_fn_fn=(lambda args: ( lambda node: 1+sum([n.sample_cost() for n in node.input_nodes]) ) ), 
                                    requires_valid_sdf=False,
                                    outputs_valid_sdf=IF_INPUTS_VALID,
                                    solid_outside_bounds=False,
                                    value_outside_bounds=0):
    assert(type(name) == str)
    assert(type(argtypes) == list)
    assert(returntype in (Solid, Field))
    for arg in argtypes:
        assert(type(arg) == type)

    #assert(callable(bounds) or type(bounds)==Bounds)
    if not callable(bounds):
        bounds = wrap(bounds)
        
    assert(callable(sample_cost_fn_fn))

    assert(callable(requires_valid_sdf) or type(requires_valid_sdf) is bool)
    if not callable(requires_valid_sdf):
        requires_valid_sdf = wrap(requires_valid_sdf)

    assert(callable(outputs_valid_sdf) or type(outputs_valid_sdf) is bool or outputs_valid_sdf==IF_INPUTS_VALID)
    assert returntype==Solid or outputs_valid_sdf==IF_INPUTS_VALID, "Function returns a field which has no SDF"
    if not callable(outputs_valid_sdf):
        outputs_valid_sdf = wrap(outputs_valid_sdf)

    assert(callable(solid_outside_bounds) or type(solid_outside_bounds) is bool)
    assert returntype==Solid or solid_outside_bounds==False, "Field can't be solid outside bounds"
    if not callable(solid_outside_bounds):
        solid_outside_bounds = wrap(solid_outside_bounds)

    assert(callable(value_outside_bounds) or type(value_outside_bounds) in (float,int))
    assert returntype==Field or value_outside_bounds==0, "Solid can't have value outside bounds"
    if not callable(value_outside_bounds):
        value_outside_bounds = wrap(value_outside_bounds)

        
    if name not in OperationRegistry:
        OperationRegistry[name] = []
        globals()[name] = lambda *args: DoOperation(name, args)

    if returntype==Solid:
        construction_funcs = Obj(bounds=bounds, sample_cost_fn=sample_cost_fn_fn, requires_valid_sdf=requires_valid_sdf, outputs_valid_sdf=outputs_valid_sdf, solid_outside_bounds=solid_outside_bounds)
    else:
        construction_funcs = Obj(bounds=bounds, sample_cost_fn=sample_cost_fn_fn, requires_valid_sdf=requires_valid_sdf, value_outside_bounds=value_outside_bounds)

    OperationRegistry[name].append( ((lambda args: GetObject(returntype, name, args, construction_funcs)), argtypes) )

#AddOperation("Discretize", (ObjType, True), [(ObjType, False)])

def Translate(obj, vec):
    return Transform(obj, Transformation(Mat2x2(1,0,0,1),vec))

def Scale(obj, vec):
    return Transform(obj, Transformation(Mat2x2(vec.x,0,0,vec.y),Vec2(0,0)))

def Rotate(obj, ang):
    return Transform(obj, Transformation(Mat2x2(math.cos(math.radians(ang)),math.sin(math.radians(ang)),-math.sin(math.radians(ang)),math.cos(math.radians(ang))),Vec2(0,0)))

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

AddOperation("Transform", Solid, [Solid, Transformation], outputs_valid_sdf=False) #todo keep sdf validity if transformation is square
AddOperation("Transform", Field, [Field, Transformation])

AddOperation("Circle", Solid, [], Bounds(-1,-1,1,1))
AddOperation("Square", Solid, [], Bounds(-1,-1,1,1))
AddOperation("Empty", Solid, [], Bounds(0,0,0,0))

AddOperation("Union2", Solid, [Solid, Solid])
AddOperation("Intersect2", Solid, [Solid, Solid])

AddOperation("Subtract", Solid, [Solid, Solid])

AddOperation("Invert", Solid, [Solid])

AddOperation("ExpandSurface", Solid, [Solid, Field, float], outputs_valid_sdf=False, requires_valid_sdf=True)

AddOperation("UniformField", Field, [float])

AddOperation("SolidToField", Field, [Solid])

AddOperation("BlurField", Field, [Field, float])

AddOperation("Add2", Field, [Field, Field])
AddOperation("Multiply2", Field, [Field, Field])
AddOperation("Max2", Field, [Field, Field])
AddOperation("Min2", Field, [Field, Field])

AddOperation("Subtract", Field, [Field, Field])

AddOperation("Invert", Field, [Field])

AddOperation("EnsureValidSDF", Solid, [Solid], requires_valid_sdf=True)

class SDFGraphNode:
    def __init__(self, node):
        self.node = node
        self.edges = set()

#while iterating you can change the outputs of the visiting node and any unvisited nodes, but not anything thats been visited already
def creation_order(graph_top):
    fringe = graph_top
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

#this should only be run one time because it edits the nodes
def Output(final, resolution=100):
    final = EnsureValidSDF(final)

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

    find_outputs(final)

    # traverse upward to figure out the resolution of each node
    final.resolution = resolution
    fringe = [final]
    resolutions_measured = {}
    while len(fringe)>0:
        next = fringe.pop(0)
        input_res = next.resolution*next.args[1].matrix.scale_factor() if next.fn=="Transform" else next.resolution
        for inp in next.input_nodes:
            inp.resolution = max(inp.resolution, input_res)
            if inp not in resolutions_measured:
                resolutions_measured[inp]=0
            resolutions_measured[inp]+=1
            if resolutions_measured[inp]==len(inp.output_nodes):
                fringe.append(inp)

    #creation_order is now valid

    sdf_graph_sink = SDFGraphNode(None)
    sdf_graph_outs = {}
    sdf_graph_mids = {}
    sdf_graph_ins = {}
    sdf_graph_source = SDFGraphNode(None)

    def add_to_sdf_graph(n, to):
        if n.outputs_valid_sdf == IF_INPUTS_VALID:
            if n not in sdf_graph_mids:
                sdf_graph_mids[n] = SDFGraphNode(n)
            sdf_graph_mids[n].edges.add(to)
        elif n.outputs_valid_sdf == False:
            if n not in sdf_graph_ins:
                sdf_graph_ins[n] = SDFGraphNode(n)
                sdf_graph_source.edges.add(sdf_graph_ins[n])
            sdf_graph_ins[n].edges.add(to)
        else:
            assert(False)

    # for n in pruned_order:
    #     if n.requires_valid_sdf and len(n.input_uncertain_solids)>0:
    #         sdf_graph_outs[n] = SDFGraphNode(n)
    #         sdf_graph_outs[n].edges.add(sdf_graph_sink)
    #         for i in n.input_uncertain_solids:
    #             add_to_sdf_graph(i, sdf_graph_outs[n])

    already = set()
    def printsdfgraph(sgn):
        ths = "TOP" if sgn==sdf_graph_source else "BOTTOM" 
        if sgn.node != None:
            ths = sgn.node.id
        st = ths
        if sgn not in already:
            st += "("
            already.add(sgn)
            for out in sgn.edges:
                st+=printsdfgraph(out)
            st += ")"
        return st

    # print( printsdfgraph(sdf_graph_source) )

    for n,delete in creation_order(graph_top):

        print(n.id + "@" + str(n.resolution) + " =", n.fn, n.args)

        #todo: define internal commands for mutable input/output; reuse buffers when possible
        for d in delete:
            print("del "+d.id)
    
    print("Output "+final.id)

    print("Exiting")
    sys.exit()


