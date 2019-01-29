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
    t(coord) = (coord[1]*canvas.spacing, coord[2]*canvas.spacing)
    for I in R
        if subtract
            canvas.grid[I] = max(canvas.grid[I], -shape[t(I)...])
        else
            canvas.grid[I] = min(canvas.grid[I], shape[t(I)...])
        end
    end
    return canvas
end

function displace!(canvas::Canvas, dist::Real, selector=(x, y)->1.0)
    for I in CartesianIndices(canvas.grid)
        canvas.grid[I] -= dist * selector(canvas.normals[1,I], canvas.normals[2,I])
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
