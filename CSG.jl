abstract type CSG{T <: AbstractFloat} end

struct Transform{T} <: CSG{T}
    child :: CSG
    x :: T
    y :: T
    matrix :: Matrix{T}
    Transform{T}(child::CSG{T}, x::Real, y::Real, m::Matrix) where {T} = new(child, x, y, m^-1)
end
function rotmatrix(r::Real)
    c = cos(r)
    s = sin(r)
    return [c s; -s c]
end
Transform(child::CSG{T}, x::Real, y::Real, r::Real=0.0) where {T} = Transform{T}(child, x, y, rotmatrix(r))


struct Circle{T} <: CSG{T}
    radius :: T
end

struct Square{T} <: CSG{T}
    radius :: T
end

#composite CSG types
struct Intersect{T} <: CSG{T}
    children :: Vector{CSG{T}}
end
struct SoftIntersect{T} <: CSG{T}
    children :: Vector{CSG{T}}
    smoothness :: T
end
struct Union{T} <: CSG{T}
    children :: Vector{CSG{T}}
end
struct SoftUnion{T} <: CSG{T}
    children :: Vector{CSG{T}}
    smoothness :: T
end
struct Negate{T} <: CSG{T}
    child :: CSG{T}
end
struct UniformSolid{T} <: CSG{T}
    filled :: Bool
end


import Base.getindex
function getindex(trans::Transform, posx::Real, posy::Real)
    posx, posy = (posx-trans.x, posy-trans.y)
    newposx, newposy = trans.matrix * [posx, posy]
    #newposx, newposy = (c * posx + s * posy,
    #                   -s * posx + c * posy)
    return trans.child[newposx, newposy]
end
getindex(csg::T, posx::Real, posy::Real) where {T <: CSG} = error("getindex not implemented for $T")
#signed distance functions
getindex(csg::Circle, posx::Real, posy::Real) = sqrt(posx*posx+posy*posy) - csg.radius
function getindex(csg::Square, pos::Vararg{Real, 2})
    inside = max(abs.(pos)...) - csg.radius
    disp = max.(abs.(pos) .- csg.radius, 0)
    return min(inside, 0) + sqrt(disp[1]*disp[1]+disp[2]*disp[2])
end
getindex(csg::Intersect, pos::Vararg{Real, 2}) = maximum(child[pos...] for child in csg.children)
getindex(csg::SoftIntersect, pos::Vararg{Real, 2}) = csg.smoothness*log(sum(exp(child[pos...]/csg.smoothness) for child in csg.children))
getindex(csg::Union, pos::Vararg{Real, 2}) = minimum(child[pos...] for child in csg.children)
getindex(csg::SoftUnion, pos::Vararg{Real, 2}) = -csg.smoothness*log(sum(exp(-child[pos...]/csg.smoothness) for child in csg.children))
getindex(csg::Negate, pos::Vararg{Real, 2}) = -csg.child[pos...]
getindex(csg::UniformSolid{T}, pos::Vararg{Real, 2}) where {T} = csg.filled ? typemin(T) : typemax(T)
