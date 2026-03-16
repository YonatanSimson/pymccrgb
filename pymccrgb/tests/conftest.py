import os

# Must be set before pymcc_lidar is loaded to force single-threaded OpenMP execution.
# SurfaceInterpolation.cpp has a data race in its parallel loop (getNextCell() called
# outside the critical section), making results non-deterministic with >1 thread.
os.environ["OMP_NUM_THREADS"] = "1"
