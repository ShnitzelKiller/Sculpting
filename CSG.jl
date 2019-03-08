include("typedefs.jl")
struct Transform{T, C<:CSG{T}} <: CSG{T}
    child :: C
    x :: T
    y :: T
    matrix :: Matrix{T}
    Transform{T}(child::C, x::Real, y::Real, m::Matrix) where {T, C<:CSG{T}} = new{T,C}(child, x, y, m^-1)
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
struct Union2{T, C<:CSG{T}, D<:CSG{T}} <: CSG{T}
    left :: C
    right :: D
end
struct SoftUnion{T} <: CSG{T}
    children :: Vector{CSG{T}}
    smoothness :: T
end
struct Negate{T, C<:CSG{T}} <: CSG{T}
    child :: C
end
struct UniformSolid{T} <: CSG{T}
    filled :: Bool
end
struct Displace{T, C<:CSG{T}, F<:Field{T}} <: CSG{T}
    child :: C
    selection :: F
    factor :: T
end


import Base.getindex
function getindex(trans::Transform{T}, posx::T, posy::T) where {T}
    posx, posy = (posx-trans.x, posy-trans.y)
    newposx, newposy = trans.matrix[1,1] * posx + trans.matrix[1,2] * posy, trans.matrix[2,1] * posx + trans.matrix[2,2] * posy
    return trans.child[newposx, newposy]
end
#signed distance functions
getindex(csg::Circle{T}, posx::T, posy::T) where {T} = sqrt(posx*posx+posy*posy) - csg.radius
function getindex(csg::Square{T}, pos::Vararg{T, 2}) where {T}
    inside = max(abs.(pos)...) - csg.radius
    disp = max.(abs.(pos) .- csg.radius, 0)
    return min(inside, 0) + sqrt(disp[1]*disp[1]+disp[2]*disp[2])
end
getindex(csg::Intersect{T}, pos::Vararg{T, 2}) where {T} = maximum(child[pos...] for child in csg.children)
getindex(csg::SoftIntersect{T}, pos::Vararg{T, 2}) where {T} = csg.smoothness*log(sum(exp(child[pos...]/csg.smoothness) for child in csg.children))
getindex(csg::Union{T}, pos::Vararg{T, 2}) where {T} = minimum(child[pos...] for child in csg.children)
getindex(csg::Union2{T}, pos::Vararg{T,2}) where {T} = min(csg.left[pos...], csg.right[pos...])
getindex(csg::SoftUnion{T}, pos::Vararg{T, 2}) where {T} = -csg.smoothness*log(sum(exp(-child[pos...]/csg.smoothness) for child in csg.children))
getindex(csg::Negate{T}, pos::Vararg{T, 2}) where {T} = -csg.child[pos...]
getindex(csg::UniformSolid{T}, pos::Vararg{T, 2}) where {T} = csg.filled ? typemin(T) : typemax(T)
getindex(csg::Displace{T}, pos::Vararg{T, 2}) where {T} = csg.child[pos...] - csg.selection[pos...] * csg.factor
