include("canvas.jl")

#TODO: Blur fields
#out of bounds values

#put maxdist into frontend

#optional: basic error checking


namespace = Dict()

function execute(cmds)
    for cmd in cmds
        println(cmd)
        if cmd["cmd"] == "create"
            if cmd["fn"] == "Transform"
                inputShape = namespace[cmd["args"][1]]
                if isa(inputShape, CSG)
                    namespace[cmd["id"]] = Transform(inputShape, 0.0, 0.0, 0.0)
                else
                    error("Transform not implemented for $(typeof(inputShape))")
                end
            elseif cmd["fn"] == "Circle"
                namespace[cmd["id"]] = Circle(1.0)
            elseif cmd["fn"] == "Square"
                namespace[cmd["id"]] = Square(1.0)
            elseif cmd["fn"] == "Union" || cmd["fn"] == "Union2"
                namespace[cmd["id"]] = Union([namespace[id] for id in cmd["args"]])
            elseif cmd["fn"] == "Intersect" || cmd["fn"] == "Intersect2"
                namespace[cmd["id"]] = Intersect([namespace[id] for id in cmd["args"]])
            elseif cmd["fn"] == "Invert"
                namespace[cmd["id"]] = Negate(namespace[cmd["args"][1]])
            elseif cmd["fn"] == "Discretize"
                shape = namespace[cmd["args"][1]]
                xlow, ylow, xhigh, yhigh = cmd["bbox"]
                if isa(shape, CSG)
                    canvas = Canvas{Float64}(xlow, ylow, xhigh, yhigh, cmd["resolution"], Inf)
                    draw!(canvas, shape)
                    namespace[cmd["id"]] = FromCanvas{Float64}(canvas)
                elseif isa(shape, Field)
                    field = GridField{Float64}(xlow, ylow, xhigh, yhigh, cmd["resolution"])
                    draw!(field, shape)
                    namespace[cmd["id"]] = field
                else
                    error("invalid argument to Discretize")
                end
            elseif cmd["fn"] == "DiscretizeAndRepairSDF" || cmd["fn"] == "EnsureValidSDFForOutput"
                shape = namespace[cmd["args"][1]]
                xlow, ylow, xhigh, yhigh = cmd["bbox"]
                if isa(shape, CSG)
                    canvas = Canvas{Float64}(xlow, ylow, xhigh, yhigh, cmd["resolution"], Inf)
                    draw!(canvas, shape)
                    update!(canvas)
                    namespace[cmd["id"]] = FromCanvas{Float64}(canvas)
                else
                    error("invalid argument to DiscretizeAndRepairSDF")
                end
            elseif cmd["fn"] == "SolidToField"
                solid = namespace[cmd["args"][1]]
                if isa(solid, CSG)
                    field = FromSolid{Float64}(solid)
                    namespace[cmd["id"]] = field
                else
                    error("SolidToField called on non-field")
                end
            elseif cmd["fn"] == "BlurField"
                #noop
                namespace[cmd["id"]] = namespace[cmd["args"][1]]
            elseif cmd["fn"] == "ExpandSurface"
                solid = namespace[cmd["args"][1]]
                field = namespace[cmd["args"][2]]
                fac = cmd["args"][3]
                if isa(solid, FromCanvas)
                    displace!(solid.canvas, fac, field)
                else
                    xlow, ylow, xhigh, yhigh = cmd["bbox"]
                    canvas = Canvas{Float64}(xlow, ylow, xhigh, yhigh, cmd["resolution"], Inf)
                    draw!(canvas, solid)
                    displace!(canvas, fac, field)
                    namespace[cmd["id"]] = FromCanvas{Float64}(canvas)
                    #error("trying to expand non-discretized solid of type $(typeof(solid))")
                end
            elseif cmd["fn"] == "UniformSolid"
                solid = UniformSolid{Float64}(cmd["args"][1])
                namespace[cmd["id"]] = solid
            else
                error("unrecognized function $(cmd["fn"])")
                exit()
            end
        elseif cmd["cmd"] == "delete"
            delete!(namespace, cmd["id"])
        elseif cmd["cmd"] == "output"
            return namespace[cmd["id"]]
        else
            error("unrecognized command type")
            exit()
        end
    end
end
