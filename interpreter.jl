include("canvas.jl")

#TODO: Blur fields
#out of bounds values
#Fix how expandSurface handles canvases (modifying them in place currently) once we know how the IR will guarantee types

#put maxdist into frontend

#optional: basic error checking


namespace = IdDict{String, Any}()

function discretize(shape::CSG, resolution, xlow, ylow, xhigh, yhigh, oob, repair=false)
    canvas = Canvas{Float64}(xlow, ylow, xhigh, yhigh, resolution, Inf)
    println("allocated canvas with resolution $resolution and dims $(canvas.dims)")
    draw!(canvas, shape)
    println("populated canvas")
    if repair
        update!(canvas)
        println("corrected SDF")
    end
    return FromCanvas{Float64}(canvas, oob) #oob: solid outside bounds
end

function discretize(field::Field, resolution, xlow, ylow, xhigh, yhigh, oob, repair=false)
    canvas = GridField{Float64}(xlow, ylow, xhigh, yhigh, resolution, oob)
    draw!(canvas, field)
    return field
end

function execute(cmds)
    for cmd in cmds
        println("$cmd\n")
        if cmd["cmd"] == "create"
            fn = cmd["fn"]
            if fn == "Transform"
                inputShape = namespace[cmd["args"][1]]
                trans = cmd["args"][2]
                mat = trans[:matrix]
                offset = trans[:translation]
                matrix = [mat[:xx] mat[:xy]; mat[:yx] mat[:yy]]
                println(matrix)
                namespace[cmd["id"]] = Transform{Float64}(inputShape, offset[:x], offset[:y], matrix)
            elseif fn == "Circle"
                namespace[cmd["id"]] = Circle{Float64}(1.0)
            elseif fn == "Square"
                namespace[cmd["id"]] = Square{Float64}(1.0)
            elseif fn == "Union2"
                left = namespace[cmd["args"][1]]
                right = namespace[cmd["args"][2]]
                namespace[cmd["id"]] = Union2(left, right)
            elseif fn == "Invert"
                shape = namespace[cmd["args"][1]]
                namespace[cmd["id"]] = Negate(shape)
            elseif fn == "SolidToField"
                solid = namespace[cmd["args"][1]]
                if isa(solid, CSG)
                    field = FromSolid(solid)
                    namespace[cmd["id"]] = field
                else
                    error("SolidToField called on non-field")
                end
            elseif fn == "BlurField"
                #noop
                namespace[cmd["id"]] = namespace[cmd["args"][1]]
            elseif fn == "ExpandSurface"
                solid = namespace[cmd["args"][1]]
                field = namespace[cmd["args"][2]]
                fac = cmd["args"][3]
                displaced = Displace(solid, field, fac)
                namespace[cmd["id"]] = displaced
            elseif fn == "UniformSolid"
                solid = UniformSolid{Float64}(cmd["args"][1])
                namespace[cmd["id"]] = solid
            elseif fn == "UniformField"
                field = UniformField{Float64}(cmd["args"][1])
                namespace[cmd["id"]] = field
            else
                error("unrecognized function $fn")
                return
            end
        elseif cmd["cmd"] == "delete"
            for id in cmd["ids"]
                delete!(namespace, id)
            end
        else
            error("unrecognized command type")
            return
        end

        if haskey(cmd, "discretize")
            properties = cmd["discretize"]
            if haskey(cmd, "oob_solid")
                oob = cmd["oob_solid"]
            elseif haskey(cmd, "oob_value")
                oob = cmd["oob_value"]
            end
            shape = namespace[cmd["id"]]
            discretized = discretize(shape, properties["resolution"], properties["bbox"]..., oob, properties["repair_sdf"])
            namespace[cmd["id"]] = discretized
        end

        if haskey(cmd, "final")
            return namespace[cmd["id"]]
        end
    end
end
