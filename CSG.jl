using LinearAlgebra

struct Transform{T <: AbstractFloat}
    x :: T
    y :: T
    rotation :: T
end
Transform(x=0.0, y=0.0, r=0.0) = Transform{Float64}(x, y, r)

function (trans::Transform)(pos::Vector)
    c = cos(trans.rotation)
    s = sin(trans.rotation)
    return [c s; -s c] * (pos - [trans.x, trans.y])
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

_map(csg::CSG, pos::Vector) = error("_map not implemented for $(typeof(csg))")
_transform(csg::CSG, pos::Vector) = csg.transform(pos)
import Base.getindex
function getindex(csg::T, pos::Real...) where {T <: CSG}
    if @generated
        if in(:transform, fieldnames(T))
            return :(_map(csg, csg.transform([pos...])))
        else
            return :(_map(csg, [pos...]))
        end
    else
        return _map(csg, in(:transform, fieldnames(T)) ? csg.transform([pos...]) : [pos...])
    end
end
#signed distance functions
_map(csg::Circle, pos::Vector) = norm(pos) - csg.radius
function _map(csg::Square, pos::Vector)
    inside = maximum(abs.(pos)) - csg.radius
    disp = max.(abs.(pos) .- csg.radius, 0)
    return min(inside, 0) + norm(disp)
end
_map(csg::Intersect, pos::Vector) = maximum(child[pos...] for child in csg.children)
_map(csg::Union, pos::Vector) = minimum(child[pos...] for child in csg.children)
_map(csg::Negate, pos::Vector) = -csg.child[pos...]
