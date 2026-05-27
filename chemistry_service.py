from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import urllib.parse

import requests
from rdkit import Chem
from rdkit.Chem import AllChem, Crippen, Descriptors, rdMolDescriptors


ALIASES = {
    "dichloro-diphenyl-trichloroethane": "DDT",
    "ddt": "DDT",
    "vitamin c": "ascorbic acid",
    "葡萄糖": "glucose",
    "右旋糖": "glucose",
    "乙醇": "ethanol",
    "酒精": "ethanol",
    "乙醛": "acetaldehyde",
    "乙酸": "acetic acid",
    "醋酸": "acetic acid",
    "甲醇": "methanol",
    "丙酮": "acetone",
    "苯": "benzene",
    "甲苯": "toluene",
    "苯酚": "phenol",
    "苯甲酸": "benzoic acid",
    "阿斯匹靈": "aspirin",
    "阿司匹林": "aspirin",
    "乙醯水楊酸": "aspirin",
    "水楊酸": "salicylic acid",
    "滴滴涕": "DDT",
    "維生素c": "ascorbic acid",
    "維生素 c": "ascorbic acid",
    "維他命c": "ascorbic acid",
    "維他命 c": "ascorbic acid",
    "抗壞血酸": "ascorbic acid",
    "咖啡因": "caffeine",
    "尼古丁": "nicotine",
    "尿素": "urea",
    "甘油": "glycerol",
    "甘油醇": "glycerol",
    "蔗糖": "sucrose",
    "果糖": "fructose",
    "乳酸": "lactic acid",
    "檸檬酸": "citric acid",
    "丙胺酸": "alanine",
    "甘胺酸": "glycine",
    "苯丙胺酸": "phenylalanine",
    "膽固醇": "cholesterol",
    "嗎啡": "morphine",
    "可待因": "codeine",
    "青黴素": "penicillin",
    "布洛芬": "ibuprofen",
    "對乙醯氨基酚": "acetaminophen",
    "乙醯胺酚": "acetaminophen",
    "撲熱息痛": "acetaminophen",
}

FUNCTIONAL_GROUPS = {
    "Alcohol": "[OX2H][CX4]",
    "Phenol": "[OX2H][c]",
    "Ether": "[OD2]([#6])[#6]",
    "Aldehyde": "[CX3H1](=O)[#6,#1]",
    "Ketone": "[#6][CX3](=O)[#6]",
    "Carboxylic acid": "[CX3](=O)[OX2H1]",
    "Ester": "[CX3](=O)[OX2][#6]",
    "Amide": "[NX3][CX3](=O)",
    "Amine": "[NX3;H2,H1,H0;!$(NC=O)]",
    "Alkene": "[CX3]=[CX3]",
    "Alkyne": "[CX2]#[CX2]",
    "Aromatic ring": "a1aaaaa1",
    "Alkyl halide": "[CX4][F,Cl,Br,I]",
    "Aryl halide": "[c][F,Cl,Br,I]",
    "Nitrile": "[CX2]#N",
    "Nitro": "[$([NX3](=O)=O),$([NX3+](=O)[O-])]",
}


class MoleculeLookupError(ValueError):
    """Raised when a molecule cannot be resolved or parsed."""


@dataclass(frozen=True)
class MoleculeIdentity:
    smiles: str
    iupac_name: str
    cid: int | str
    source: str


def normalize_name(name: str) -> str:
    clean_name = " ".join(name.strip().split())
    if not clean_name:
        raise MoleculeLookupError("Please enter a molecule name.")
    return ALIASES.get(clean_name.lower(), clean_name)


def get_smiles(name: str) -> MoleculeIdentity:
    search_name = normalize_name(name)
    encoded = urllib.parse.quote(search_name)

    pubchem_result = _lookup_pubchem(encoded)
    if pubchem_result:
        return pubchem_result

    cactus_result = _lookup_cactus(encoded)
    if cactus_result:
        return cactus_result

    opsin_result = _lookup_opsin(encoded)
    if opsin_result:
        return opsin_result

    raise MoleculeLookupError(f"Could not find a SMILES structure for '{name}'.")


def build_molecule_card(name: str) -> dict[str, Any]:
    identity = get_smiles(name)
    mol = Chem.MolFromSmiles(identity.smiles)

    if mol is None:
        raise MoleculeLookupError("RDKit could not parse the resolved SMILES.")

    mol_h = Chem.AddHs(mol)
    params = AllChem.ETKDGv3()
    params.randomSeed = 2026

    status = AllChem.EmbedMolecule(mol_h, params)
    if status != 0:
        status = AllChem.EmbedMolecule(mol_h, randomSeed=2026, useRandomCoords=True)
    if status != 0:
        raise MoleculeLookupError("RDKit could not generate a 3D conformer.")

    _optimize_molecule(mol_h)
    functional_groups = detect_functional_groups(mol)
    notes = build_teaching_notes(functional_groups)
    notes_zh = build_teaching_notes_zh(functional_groups)

    return {
        "query": name,
        "display_name": normalize_name(name),
        "iupac_name": identity.iupac_name,
        "smiles": identity.smiles,
        "source": identity.source,
        "mol_block": Chem.MolToMolBlock(mol_h),
        "properties": {
            "formula": rdMolDescriptors.CalcMolFormula(mol),
            "molecular_weight": round(Descriptors.MolWt(mol), 2),
            "exact_mass": round(rdMolDescriptors.CalcExactMolWt(mol), 4),
            "mol_logp": round(Crippen.MolLogP(mol), 2),
            "tpsa": round(rdMolDescriptors.CalcTPSA(mol), 2),
            "h_bond_donor": rdMolDescriptors.CalcNumHBD(mol),
            "h_bond_acceptor": rdMolDescriptors.CalcNumHBA(mol),
            "rotatable_bonds": rdMolDescriptors.CalcNumRotatableBonds(mol),
            "rings": rdMolDescriptors.CalcNumRings(mol),
            "aromatic_rings": rdMolDescriptors.CalcNumAromaticRings(mol),
            "fraction_csp3": round(rdMolDescriptors.CalcFractionCSP3(mol), 3),
            "pubchem_cid": identity.cid,
        },
        "functional_groups": functional_groups,
        "teaching_notes": notes,
        "teaching_notes_zh": notes_zh,
    }


def detect_functional_groups(mol: Chem.Mol) -> list[str]:
    found = []
    for group_name, smarts in FUNCTIONAL_GROUPS.items():
        pattern = Chem.MolFromSmarts(smarts)
        if pattern and mol.HasSubstructMatch(pattern):
            found.append(group_name)
    return found


def build_teaching_notes(functional_groups: list[str]) -> list[str]:
    notes = []
    groups = set(functional_groups)

    if "Alcohol" in groups:
        notes.append("Alcohol: hydrogen bonding; oxidation / esterification possible.")
    if "Aromatic ring" in groups:
        notes.append("Aromatic ring: resonance and electrophilic aromatic substitution.")
    if "Carboxylic acid" in groups:
        notes.append("Carboxylic acid: acidic proton; resonance-stabilized conjugate base.")
    if "Ester" in groups:
        notes.append("Ester: hydrolysis and nucleophilic acyl substitution.")
    if "Amide" in groups:
        notes.append("Amide: resonance lowers nitrogen basicity.")
    if "Amine" in groups:
        notes.append("Amine: usually basic and nucleophilic.")
    if "Alkyl halide" in groups or "Aryl halide" in groups:
        notes.append(
            "Halogenated compound: useful for discussing polarity, "
            "lipophilicity, and substitution patterns."
        )

    return notes or ["Inspect structure manually for reaction sites."]


def build_teaching_notes_zh(functional_groups: list[str]) -> list[str]:
    notes = []
    groups = set(functional_groups)

    if "Alcohol" in groups:
        notes.append("醇類：可形成氫鍵，常用於討論氧化反應與酯化反應。")
    if "Aromatic ring" in groups:
        notes.append("芳香環：具有共振穩定性，可用於說明親電子芳香取代反應。")
    if "Carboxylic acid" in groups:
        notes.append("羧酸：含有酸性氫，去質子化後的共軛鹼可由共振穩定。")
    if "Ester" in groups:
        notes.append("酯類：可用於說明水解反應與親核醯基取代反應。")
    if "Amide" in groups:
        notes.append("醯胺：因共振效應降低氮原子的鹼性。")
    if "Amine" in groups:
        notes.append("胺類：通常具有鹼性與親核性。")
    if "Alkyl halide" in groups or "Aryl halide" in groups:
        notes.append("含鹵素化合物：適合討論極性、脂溶性與取代位置對性質的影響。")

    return notes or ["請手動觀察結構中的可能反應位置。"]


def _lookup_pubchem(encoded_name: str) -> MoleculeIdentity | None:
    cid_url = (
        "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
        f"{encoded_name}/cids/JSON"
    )
    response = _safe_get(cid_url)
    if not response:
        return None

    cid_list = response.json().get("IdentifierList", {}).get("CID", [])
    if not cid_list:
        return None

    cid = cid_list[0]
    prop_url = (
        "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/"
        f"{cid}/property/IsomericSMILES,CanonicalSMILES,IUPACName/JSON"
    )
    prop_response = _safe_get(prop_url)
    if not prop_response:
        return None

    properties = prop_response.json().get("PropertyTable", {}).get("Properties", [])
    if not properties:
        return None

    item = properties[0]
    smiles = (
        item.get("IsomericSMILES")
        or item.get("CanonicalSMILES")
        or item.get("SMILES")
        or item.get("ConnectivitySMILES")
    )
    if not smiles:
        return None

    return MoleculeIdentity(
        smiles=smiles,
        iupac_name=item.get("IUPACName") or "Unknown",
        cid=cid,
        source="PubChem",
    )


def _lookup_cactus(encoded_name: str) -> MoleculeIdentity | None:
    url = f"https://cactus.nci.nih.gov/chemical/structure/{encoded_name}/smiles"
    response = _safe_get(url)
    if not response:
        return None

    smiles = response.text.strip()
    if not smiles or smiles.lower().startswith("<!doctype"):
        return None

    return MoleculeIdentity(
        smiles=smiles,
        iupac_name="Unknown",
        cid="Unknown",
        source="NCI/Cactus",
    )


def _lookup_opsin(encoded_name: str) -> MoleculeIdentity | None:
    url = f"https://opsin.ch.cam.ac.uk/opsin/{encoded_name}.json"
    response = _safe_get(url)
    if not response:
        return None

    data = response.json()
    smiles = data.get("smiles")
    if not smiles:
        return None

    return MoleculeIdentity(
        smiles=smiles,
        iupac_name=data.get("iupacName") or "Unknown",
        cid="Unknown",
        source="OPSIN",
    )


def _safe_get(url: str) -> requests.Response | None:
    try:
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            return response
    except requests.RequestException:
        return None
    return None


def _optimize_molecule(mol: Chem.Mol) -> None:
    try:
        AllChem.MMFFOptimizeMolecule(mol)
    except Exception:
        try:
            AllChem.UFFOptimizeMolecule(mol)
        except Exception:
            return
