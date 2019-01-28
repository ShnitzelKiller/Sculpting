include("CSG.jl")
include("fast_marching.jl")
include("mathutil.jl")

struct Canvas{T <: AbstractFloat}
    spacing::T
    dims::Vector{T}
    maxdist::T
    grid::Array{T, 2}
    normals::Array{T, 3}
    function Canvas{T}(height::Real, width::Real, spacing::Real, maxdist::Real) where {T <: AbstractFloat}
        dims = [height, width]
        resolution = Int.(ceil.(dims./spacing))
        grid = fill(maxdist, resolution...)
        normals = fill(NaN, 2, resolution...)
        new{T}(spacing, dims, maxdist, grid, normals)
    end
end
Canvas(height::Real, width::Real, spacing::Real, maxdist::Real) = Canvas{Float64}(height, width, spacing, maxdist)

function draw!(canvas::Canvas, shape::CSG, subtract::Bool=false)
    R = CartesianIndices(canvas.grid)
    for I in R
        coords = [I[1],I[2]] * canvas.spacing
        canvas.grid[I] = (subtract ? max : min)(canvas.grid[I], shape[coords...])
    end
    return canvas
end

function clear!(canvas::Canvas)
    canvas.grid .= canvas.maxdist
    return canvas
end

function update_sdf!(canvas::Canvas)
    fast_marching!(canvas.grid, canvas.spacing, canvas.maxdist)
    canvas.grid .= -canvas.grid
    fast_marching!(canvas.grid, canvas.spacing, canvas.maxdist)
    canvas.grid .= -canvas.grid
    return canvas
end

function update_normals!(canvas::Canvas)
    canvas.normals .= partial(canvas.grid, 1, 2) / canvas.spacing
end
