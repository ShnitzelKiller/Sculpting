function precompile_pkgs()
    for pkg in collect(keys(Pkg.installed()))
        if !isdefined(Main, Symbol(pkg)) && pkg != "Compat.jl"
            @info("Importing $(pkg)...")
            try (@eval import $(Symbol(pkg))) catch end
        end
    end
end
