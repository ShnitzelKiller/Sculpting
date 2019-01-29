include("canvas.jl")
using Plots
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

canvas = Canvas(10, 10, 0.05, 4)
circle1 = Circle(3.0, Transform(5, 5))
circle2 = Circle(3.0, Transform(5, 7))
shape = Intersect([circle1, Negate(circle2)], Transform())
draw!(canvas, shape)
update_sdf!(canvas)
update_normals!(canvas)
displace!(canvas, 1.0)
square = Square(1.0, Transform(5, 5))
draw!(canvas, square, true)
update_sdf!(canvas)
update_normals!(canvas)
displace!(canvas, -1.0)
image = display_normals(canvas.normals, canvas.grid);
plot(image, aspect_ratio=:equal)
