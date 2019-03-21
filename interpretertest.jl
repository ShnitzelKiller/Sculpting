using PyCall
sys = pyimport("sys")
path = sys[:path]
pathvec = PyVector(path)
pushfirst!(pathvec, "")
sys[:path] = pathvec
ex = pyimport("examples")
include("interpreter.jl")

using Images
function display_normals!(image::Matrix{RGB{T}}, normals::Array{T,3}, dists::Matrix{T}) where {T <: AbstractFloat}
    for I in CartesianIndices(image)
        rg = @view normals[:,I]
        dist = dists[I]
        fac = dist < 0 ? 0.5 : 1.0
        t(x) = (x*0.3+0.5)*fac
        image[I] = RGB(t(rg[1]), t(rg[2]), fac*0.5)
    end
    return image
end
function display_normals(normals::Array{T,3}, dists::Matrix{T}) where {T <: AbstractFloat}
    image = Array{RGB{T}}(undef, size(normals)[2:end]...)::Array{RGB{T}, 2}
    return display_normals!(image, normals, dists)
end
display_normals(canvas::Canvas) = display_normals(canvas.normals, canvas.grid)

cmds = ex[:getCmds2]()

result = @time execute(cmds)
println("finished processing")

update!(result.canvas)
image = display_normals(result.canvas)
display(image)


cmds = ex[:getCmds5]()

result = @time execute(cmds)
println("finished processing")

update!(result.canvas)
image = display_normals(result.canvas)
display(image)
