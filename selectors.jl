include("typedefs.jl")
include("mathutil.jl")

function selectnorm(angle, p)
    c, s = cos(angle), sin(angle)
    f = let c = c, s = s #prevent boxing of closure variables, whatever that means
        (nx,ny) -> max(nx*c+ny*s, 0) ^ p
    end
    return f
end
function selectnorm_twosided(angle, p)
    c, s = cos(angle), sin(angle)
    f = let c = c, s = s #prevent boxing of closure variables, whatever that means
        (nx,ny) -> abs(nx*c+ny*s) ^ p
    end
    return f
end

struct FromSolid{T, C<:CSG{T}} <: Field{T}
    solid :: C
end
struct GridField{T} <: Field{T}
    data :: Matrix{T}
    offset :: Vector{T}
    spacing :: T
    function GridField{T}(xlow::Real, ylow::Real, xhigh::Real, yhigh::Real, resolution::Real) where {T <: AbstractFloat}
        dims = [yhigh - ylow, xhigh - xlow]
        gridSize = Int.(ceil.(resolution .* dims))
        yhigh, xhigh = [ylow, xlow] + (gridSize[2]-1)/resolution #correct positions
        grid = zeros(gridSize...)
        new{T}(grid, [ylow, xlow], 1/resolution)
    end
end
function draw!(gridfield::GridField, f::Field)
    R = CartesianIndices(gridfield.data)
    t(coord) = (coord[2]*gridfield.spacing + gridfield.offset[2], coord[1]*gridfield.spacing + gridfield.offset[1])
    for I in R
        gridfield.data[I] = f[t(I)...]
    end
end
getindex(field::FromSolid{T}, posx::Real, posy::Real) where {T} = convert(T, field.solid[posx, posy] < 0)
getindex(field::GridField{T}, posx::Real, posy::Real) where {T} = interpolate(field.data, (posy-field.offset[1])/field.spacing, (posx-field.offset[2])/field.spacing)
