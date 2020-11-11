#!/bin/bash
mkdir -p ${PREFIX}/share/iprpy
python ${RECIPE_DIR}/generate_csv.py
cp "potentials_lammps.csv" ${PREFIX}/share/iprpy 
cp -r potential_LAMMPS ${PREFIX}/share/iprpy
cp -r Potential ${PREFIX}/share/iprpy
cp -r Citation ${PREFIX}/share/iprpy
