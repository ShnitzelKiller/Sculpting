import Base.getindex
abstract type Field{T<:AbstractFloat} end
getindex(field::Field{Y}, posx::Y, posy::Y) where {Y} = error("getindex not implemented for $(typeof(field))")

abstract type CSG{T <: AbstractFloat} end
getindex(csg::CSG{Y}, posx::Y, posy::Y) where {Y} = error("getindex not implemented for $(typeof(csg))")
