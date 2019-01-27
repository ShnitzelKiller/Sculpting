include("CSG.jl")
include("fast_marching.jl")

function partial(A, dim)
    B = similar(A)
    R = CartesianIndices(A)
    Ifirst, Ilast = first(R), last(R)
    I1 = CartesianIndex([i == dim ? 1 : 0 for i=1:ndims(A)]...)
    for I in R
        B[I] = A[min(I+I1, Ilast)] - A[max(I-I1, Ifirst)]
    end
    for I in Ifirst+I1:Ilast-I1
        B[I] /= 2
    end
    return B
end

struct Canvas{T <: AbstractFloat}
    spacing::T
    dims::Vector{T}
    maxdist::T
    grid::Array{T, 2}
    function Canvas{T}(height::Real, width::Real, spacing::Real, maxdist::Real=1.0) where {T <: AbstractFloat}
        dims = [height, width]
        resolution = Int.(ceil.(dims./spacing))
        grid = fill(maxdist, resolution...)
        new{T}(spacing, dims, maxdist, grid)
    end
end

function draw!(canvas::Canvas, shape::CSG, subtract::Bool=false)
    R = CartesianIndices(canvas.grid)
    for I in R
        coords = [I[1],I[2]] * canvas.spacing
        canvas.grid[I] = (subtract ? max : min)(canvas.grid[I], shape[coords...])
    end
end

function update!(canvas::Canvas)
    fast_marching!(canvas.grid, canvas.spacing, canvas.maxdist)
    canvas.grid .= -canvas.grid
    fast_marching!(canvas.grid, canvas.spacing, canvas.maxdist)
    canvas.grid .= -canvas.grid
end
