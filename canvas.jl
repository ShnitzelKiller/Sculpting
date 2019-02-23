include("CSG.jl")
include("fast_marching.jl")
include("mathutil.jl")
include("selectors.jl")

struct Canvas{T <: AbstractFloat}
    spacing::T
    dims::Vector{T}
    offset::Vector{T}
    maxdist::T
    grid::Array{T, 2}
    normals::Array{T, 3}
    function Canvas{T}(xlow::Real, ylow::Real, xhigh::Real, yhigh::Real, resolution::Real, maxdist::Real) where {T <: AbstractFloat}
        dims = [yhigh - ylow, xhigh - xlow]
        gridSize = Int.(ceil.(dims .* resolution))
        yhigh, xhigh = [ylow, xlow] + (gridSize .- 1)/resolution #correct positions
        grid = fill(maxdist, gridSize...)
        normals = fill(NaN, 2, gridSize...)
        new{T}(1/resolution, [yhigh-ylow, xhigh-xlow], [ylow, xlow], maxdist, grid, normals)
    end
end
Canvas(height::Real, width::Real, spacing::Real, maxdist::Real) = Canvas{Float64}(height, width, spacing, maxdist)

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
function update!(canvas::Canvas)
    update_sdf!(canvas)
    update_normals!(canvas)
end

function draw!(canvas::Canvas, shape::CSG; subtract::Bool=false, smoothness::Real=0)
    R = CartesianIndices(canvas.grid)
    t(coord) = (coord[2]*canvas.spacing + canvas.offset[2], coord[1]*canvas.spacing + canvas.offset[1])
    if smoothness <= 0
        if subtract
            for I in R
                canvas.grid[I] = max(canvas.grid[I], -shape[t(I)...])
            end
        else
            for I in R
                canvas.grid[I] = min(canvas.grid[I], shape[t(I)...])
            end
        end
    else
        if subtract
            for I in R
                canvas.grid[I] = log(exp(canvas.grid[I]/smoothness) + exp(-shape[t(I)...]/smoothness))*smoothness
            end
        else
            for I in R
                canvas.grid[I] = -log(exp(-canvas.grid[I]/smoothness) + exp(-shape[t(I)...]/smoothness))*smoothness
            end
        end
    end
    return canvas
end

function displace!(canvas::Canvas, dist::Real)
    canvas.grid .-= dist
    #update!(canvas)
    return canvas
end

function displace!(canvas::Canvas, dist::Real, selector)
    for I in CartesianIndices(canvas.grid)
        canvas.grid[I] -= dist * selector(canvas.normals[1,I], canvas.normals[2,I])
    end
    #update!(canvas)
    return canvas
end

function displace!(canvas::Canvas, dist::Real, selector::Field)
    t(coord) = (coord[2]*canvas.spacing + canvas.offset[2], coord[1]*canvas.spacing + canvas.offset[1])
    for I in CartesianIndices(canvas.grid)
        canvas.grid[I] -= dist * selector[t(I)...]
    end
    #update!(canvas)
    return canvas
end

function clear!(canvas::Canvas)
    canvas.grid .= canvas.maxdist
    canvas.normals .= NaN
    return canvas
end

##canvas based CSG definition

struct FromCanvas{T} <: CSG{T}
    canvas :: Canvas{T}
end
function getindex(csg::FromCanvas{T}, posx::Real, posy::Real) where {T}
    return interpolate(csg.canvas.grid, (posy-csg.canvas.offset[1])/csg.canvas.spacing, (posx-csg.canvas.offset[2])/csg.canvas.spacing)
end
