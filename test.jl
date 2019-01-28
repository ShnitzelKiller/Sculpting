include("canvas.jl")
using Plots
function display_normals(image, normals, dists, thresh)
    for I in CartesianIndices(image)
        rg = @view normals[:,I]
        dist = dists[I]
        fac = dist < 0 ? 0.5 : 1.0
        image[I] = RGB((rg[1]*0.3+0.5)*fac, (rg[2]*0.3+0.5)*fac, fac*0.5)
    end
    return image
end
function display_normals(normals, dists, thresh)
    image = Array{RGB{eltype(normals)}}(undef, size(normals)[2:end]...)::Array{RGB{eltype(normals)}, 2}
    return display_normals(image, normals, dists, thresh)
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
image = display_normals(canvas.normals, canvas.grid, 0.1);
plot(image)