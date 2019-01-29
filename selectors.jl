function selectnorm(angle, p)
    c, s = cos(angle), sin(angle)
    f = let c = c, s = s #prevent boxiing of closure variables, whatever that means
        (nx,ny) -> max(nx*c+ny*s, 0) ^ p
    end
    return f
end
