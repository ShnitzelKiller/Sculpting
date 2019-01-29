struct Transform{T <: AbstractFloat}
    x :: T
    y :: T
    rotation :: T
end
Transform(x=0.0, y=0.0, r=0.0) = Transform{Float64}(x, y, r)

function (trans::Transform)(posx::Real, posy::Real)
    c = cos(trans.rotation)
    s = sin(trans.rotation)
    newpos = (c * posx + s * posy - trans.x,
              -s * posx + c * posy - trans.y)
    return newpos
end


abstract type CSG{T <: AbstractFloat} end

struct Circle{T} <: CSG{T}
    radius :: T
    transform :: Transform{T}
end

struct Square{T} <: CSG{T}
    radius :: T
    transform :: Transform{T}
end

#composite CSG types
struct Intersect{T} <: CSG{T}
    children :: Vector{CSG{T}}
    transform :: Transform{T}
end
struct Union{T} <: CSG{T}
    children :: Vector{CSG{T}}
    transform :: Transform{T}
end
struct Negate{T} <: CSG{T}
    child :: CSG{T}
end

_map(csg::CSG, pos::Vararg{Real, 2}) = error("_map not implemented for $(typeof(csg))")
import Base.getindex
function getindex(csg::T, posx::Real, posy::Real) where {T <: CSG}
    if @generated
        if in(:transform, fieldnames(T))
            return :(_map(csg, csg.transform(posx, posy)...))
        else
            return :(_map(csg, posx, posy))
        end
    else
        return _map(csg, (in(:transform, fieldnames(T)) ? csg.transform(posx, posy) : (posx, posy))...)
    end
end
#signed distance functions
_map(csg::Circle, posx::Real, posy::Real) = sqrt(posx*posx+posy*posy) - csg.radius
function _map(csg::Square, pos::Vararg{Real, 2})
    inside = max(abs.(pos)...) - csg.radius
    disp = max.(abs.(pos) .- csg.radius, 0)
    return min(inside, 0) + norm(disp)
end
_map(csg::Intersect, pos::Vararg{Real, 2}) = maximum(child[pos...] for child in csg.children)
_map(csg::Union, pos::Vararg{Real, 2}) = minimum(child[pos...] for child in csg.children)
_map(csg::Negate, pos::Vararg{Real, 2}) = -csg.child[pos...]
