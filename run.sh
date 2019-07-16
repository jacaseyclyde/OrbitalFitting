#!/bin/sh
#SBATCH --partition=nodes
#SBATCH -n 126
#SBATCH --time=24:00:00
#SBATCH --job-name=cnd_apsides
#SBATCH --output=cnd_apsides.out
#SBATCH --error=cnd_apsides.err
#SBATCH --mail-user=james.casey-clyde@sjsu.edu
#SBATCH --mail-type=ALL

module purge

module load intel-python3
conda activate mcorbit
module load mpich/intel

mpiexec python3 mcorbit/main.py --mpi -d ~/MCOrbit/dat/ --nmax 300000 --walkers 504 --out apsides --sample
