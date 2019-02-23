include("canvas.jl")

#TODO: Blur fields
#out of bounds values
#Fix how expandSurface handles canvases (modifying them in place currently) once we know how the IR will guarantee types

#put maxdist into frontend

#optional: basic error checking


namespace = Dict()

function discretize(shape::CSG, resolution, xlow, ylow, xhigh, yhigh, repair=false)
    canvas = Canvas{Float64}(xlow, ylow, xhigh, yhigh, resolution, Inf)
    println("allocated canvas with resolution $resolution and dims $(canvas.dims)")
    draw!(canvas, shape)
    println("populated canvas")
    if repair
        update!(canvas)
        println("corrected SDF")
    end
    return canvas
end

function discretize(field::Field, resolution, xlow, ylow, xhigh, yhigh)
    field = GridField{Float64}(xlow, ylow, xhigh, yhigh, resolution)
    draw!(field, shape)
    return field
end

function execute(cmds)
    for cmd in cmds
        println(cmd)
        if cmd["cmd"] == "create"
            if cmd["fn"] == "Transform"
                inputShape = namespace[cmd["args"][1]]
                if isa(inputShape, CSG)
                    trans = cmd["args"][2]
                    mat = trans[:matrix]
                    offset = trans[:translation]
                    matrix = [mat[:xx] mat[:xy]; mat[:yx] mat[:yy]]
                    print("transformation matrix: $matrix")
                    namespace[cmd["id"]] = Transform{Float64}(inputShape, offset[:x], offset[:y], matrix)
                else
                    error("Transform not implemented for $(typeof(inputShape))")
                end
            elseif cmd["fn"] == "Circle"
                namespace[cmd["id"]] = Circle{Float64}(1.0)
            elseif cmd["fn"] == "Square"
                namespace[cmd["id"]] = Square{Float64}(1.0)
            elseif cmd["fn"] == "Union2"
                left = namespace[cmd["args"][1]]
                right = namespace[cmd["args"][2]]
                namespace[cmd["id"]] = Union2{Float64, typeof(left), typeof(right)}(left, right)
            elseif cmd["fn"] == "Invert"
                shape = namespace[cmd["args"][1]]
                namespace[cmd["id"]] = Negate{Float64, typeof(shape)}(shape)
            elseif cmd["fn"] == "Discretize"
                shape = namespace[cmd["args"][1]]
                discretized = discretize(shape, cmd["resolution"], cmd["bbox"]...)
                namespace[cmd["id"]] = FromCanvas{Float64}(discretized)
            elseif cmd["fn"] == "DiscretizeAndRepairSDF"
                shape = namespace[cmd["args"][1]]
                discretized = discretize(shape, cmd["resolution"], cmd["bbox"]..., true)
                namespace[cmd["id"]] = FromCanvas{Float64}(discretized)
            elseif cmd["fn"] == "SolidToField"
                solid = namespace[cmd["args"][1]]
                if isa(solid, CSG)
                    field = FromSolid{Float64, typeof(solid)}(solid)
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
                displaced = Displace{Float64, typeof(solid), typeof(field)}(solid, field, fac)
                namespace[cmd["id"]] = displaced
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
            result = namespace[cmd["id"]]
            if isa(result, FromCanvas)
                return result.canvas
            elseif isa(result, CSG)
                return discretize(result, cmd["resolution"], cmd["bbox"]..., true)
            else
                error("output not a solid")
            end
        else
            error("unrecognized command type")
            exit()
        end
        println()

    end
end
