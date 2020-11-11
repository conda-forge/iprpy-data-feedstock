import os
import potentials
import pandas

def get_list_of_potentials(path):
    settings = potentials.Settings()
    settings.set_local(True)
    settings.set_remote(False)
    if ".NISTpotentials" in str(settings.library_directory):
        settings.set_library_directory(path)
    potdb = potentials.Database(load=True, remote=False, verbose=True)
    return potdb, potdb.get_lammps_potentials()

def get_lammps_config(pot):
    pot_str_lst = pot.pair_info().replace(pot.pot_dir + "/", "").split("\n")
    return [l + "\n" for l in pot_str_lst if 'mass' not in l and l != ""]

def get_file_names(pot):
    file_lst = []
    if pot.pot_dir != "":
        for l in pot.pair_info().split("\n"):
            if pot.pot_dir in l:
                for s in l.split():
                    if pot.pot_dir in s: 
                        file_lst.append("potential_LAMMPS" + s.replace(os.path.dirname(pot.pot_dir), ""))
    return file_lst

def get_name(pot):
    return pot.asdict()["id"]

def get_species(pot):
    return pot.asdict()["elements"]

def get_model(pot):
    if pot.asdict()['pair_style'] == 'kim':
        return "OPENKIM"
    else: 
        return "NISTiprpy"

def get_citations(pot, potdb):
    try:
        pot_el = potdb.get_potential(id=pot.asdict()['potid'])
    except ValueError:
        return None
    return [c.asdict() for c in pot_el.asdict()["citations"]]

def pyiron_potentials(pot_lst, potdb):
    config_lst, file_name_lst, model_lst, name_lst, species_lst, citations_lst = [], [], [], [], [], []
    for pot in pot_lst:
        config_lst.append(get_lammps_config(pot=pot))
        file_name_lst.append(get_file_names(pot=pot))
        model_lst.append(get_model(pot=pot))
        name_lst.append(get_name(pot=pot))
        species_lst.append(get_species(pot=pot))
        citations_lst.append(get_citations(pot=pot, potdb=potdb))
    return pandas.DataFrame({
        "Config": config_lst, 
        "Filename": file_name_lst, 
        "Model": model_lst, 
        "Name": name_lst, 
        "Species": species_lst, 
        "Citations": citations_lst
    })


if __name__ == "__main__":
    path = os.path.abspath(os.getcwd())
    potdb, pot_lst = get_list_of_potentials(path=path)
    df = pyiron_potentials(pot_lst=pot_lst, potdb=potdb)
    df.to_csv("potentials_lammps.csv")
