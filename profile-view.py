import pstats
p = pstats.Stats("profile.dat")

p.strip_dirs().sort_stats("tottime").print_stats()
