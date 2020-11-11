#!/bin/bash
mkdir -p ${PREFIX}/share/iprpy
python generate_csv.py
cp "potentials_lammps.csv" ${PREFIX}/share/iprpy 
cp -r potential_LAMMPS ${PREFIX}/share/iprpy
cp -r Potential ${PREFIX}/share/iprpy
cp -r Citation ${PREFIX}/share/iprpy
