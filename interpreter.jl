include("canvas.jl")

#TODO: implement transforms properly
#implement fields
#implement interpolation of canvases

#put maxdist into frontend

#optional: basic error checking


namespace::Dict = Dict()

function execute(cmds)
    for cmd in cmds
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
            elseif cmd["fn"] == "Union"
                namespace[cmd["id"]] = Union(namespace[id] for id in cmd["args"])
            elseif cmd["fn"] == "Intersect"
                namespace[cmd["id"]] = Intersect(namespace[id] for id in cmd["args"])
            elseif cmd["fn"] == "Union"
                namespace[cmd["id"]] = Union(namespace[id] for id in cmd["args"])
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
                    error("invalid argument to discretize")
                end
            elseif cmd["fn"] == "SolidToField"
                solid = namespace[cmd["args"][1]]
                if isa(solid, CSG)
                    field = FromSolid{Float64}(solid)
                    namespace[cmd["id"]] = field
                else
                    error("SolidToField called on non-field")
                end
            else
                error("unrecognized function")
                exit()
            end
        elseif cmd["cmd"] == "delete"
            delete!(namespace, cmd["id"])
        elseif cmd["cmd"] == "output"
            return namespace[cmd["id"]]
        else
            error("unrecognized command")
            exit()
        end
    end
end
