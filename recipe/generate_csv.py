import os
import re
from mendeleev.fetch import fetch_table
import edn_format
import kimpy
import potentials
import pandas

def get_list_of_potentials(path):
    settings = potentials.Settings.Settings()
    settings.set_local(True)
    settings.set_remote(False)
    # if ".NISTpotentials" in str(settings.library_directory):
    #     settings.set_library_directory(path)
    potdb = potentials.Database(load=True, remote=False, verbose=True)
    return potdb, potdb.get_lammps_potentials()

def get_lammps_config(pot):
    if pot.asdict()['pair_style'] == 'kim':
        return ["pair_style kim " + pot.asdict()["id"] + "\n", "pair_coeff * * " + " ".join(pot.asdict()["elements"]) + "\n"]
    else:
        pot_str_lst = pot.pair_info().replace(pot.pot_dir + "/", "").split("\n")
        return [l + "\n" for l in pot_str_lst if 'mass' not in l and l is not ""]

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

def convert_citation(entry_dict):
    cite_dict = {k: entry_dict[k] for k in ['title', 'journal', 'volume', 'pages', 'number', 'doi', 'publisher', 'url', 'year'] if k in entry_dict.keys()}
    cite_dict['author'] = entry_dict['author'].split(" and ")
    return {entry_dict["ID"]: cite_dict}
    
def get_citations(pot, potdb):
    try:
        pot_el = potdb.get_potential(id=pot.asdict()['potid'])
    except ValueError:
        return None
    return [convert_citation(entry_dict=c.asdict()) for c in pot_el.asdict()["citations"]]

def get_openkim_lammps_parameter(p, element_lst):
    el_lst = re.findall('[A-Z][^A-Z]*', p.split('__')[0].split('_')[-1])
    if all(el in element_lst for el in el_lst):
        return el_lst, ["pair_style kim " + p + "\n", "pair_coeff * * " + " ".join(el_lst) + "\n"]
    else: 
        return [], []

def get_openkim_citation(p, it, col):
    extent, error = col.cache_list_of_item_metadata_files(it, p)
    if error == 0:
        cite_lst = []
        for i in range(extent):
            out = col.get_item_metadata_file(i)
            file_name, file_length, file_raw_data, avail_as_str, file_str, error = out
            if file_name == "kimspec.edn":
                edn_dict = edn_format.loads(file_str)
                if "source-citations" in edn_dict.keys():
                    for cite in edn_dict["source-citations"]:
                        cite_dict = {k: cite[k] for k in ["title", "volume", "year", "journal", "doi"] if k in cite.keys()}
                        cite_dict["author"] = cite['author'].split("and")
                        if "issue" in cite.keys():
                            cite_dict["number"] = cite["issue"]
                        name = cite_dict["author"][0].split()[-1] + "_" + cite_dict["year"]
                        cite_lst.append({name: cite_dict})
        return cite_lst
    else:
        return []

def get_openkim_potential_lst(col):
    potential_lst = []
    for it in [
        kimpy.collection_item_type.portableModel,
        kimpy.collection_item_type.simulatorModel,
    ]:
        extent, error = col.cache_list_of_item_names_by_type(it)
        for i in range(extent):
            name, error = col.get_item_name_by_type(i)
            potential_lst.append([it, name])
    return potential_lst
    
def pyiron_potentials(pot_lst, potdb):
    config_lst, file_name_lst, model_lst, name_lst, species_lst, citations_lst = [], [], [], [], [], []
    for pot in pot_lst:
        pot_model = get_model(pot=pot)
        if pot_model == "NISTiprpy":
            config_lst.append(get_lammps_config(pot=pot))
            file_name_lst.append(get_file_names(pot=pot))
            model_lst.append(pot_model)
            name_lst.append(get_name(pot=pot))
            species_lst.append(get_species(pot=pot))
            citations_lst.append(get_citations(pot=pot, potdb=potdb))
    col, error = kimpy.collections.create()
    ptable = fetch_table('elements')
    element_lst = ptable.symbol.tolist()
    for pit in get_openkim_potential_lst(col=col):
        it, p = pit
        el_lst, pot_str = get_openkim_lammps_parameter(p=p, element_lst=element_lst)
        species_lst.append(el_lst)
        config_lst.append(pot_str)
        file_name_lst.append([])
        model_lst.append('OPENKIM')
        name_lst.append(p)
        citations_lst.append(get_openkim_citation(p=p, it=it, col=col))
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
