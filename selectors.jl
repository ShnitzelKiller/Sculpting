function selectnorm(angle, p)
    c, s = cos(angle), sin(angle)
    return (nx,ny) -> max(nx*c+ny*s, 0) ^ p
end
