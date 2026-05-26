from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors, Crippen, rdMolDescriptors
import requests
import urllib.parse
import os
import json

MOLECULE_NAME = "DDT"
OUTPUT_DIR = "chem_flashcard_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_smiles(name):
    aliases = {
        "Dichloro-Diphenyl-Trichloroethane": "DDT",
        "dichloro-diphenyl-trichloroethane": "DDT",
        "ddt": "DDT",
        "Vitamin C": "ascorbic acid",
        "vitamin c": "ascorbic acid",
    }

    search_name = aliases.get(name, name)
    encoded = urllib.parse.quote(search_name)

    cid_url = (
        "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
        f"{encoded}/cids/JSON"
    )

    r = requests.get(cid_url, timeout=20)

    if r.status_code == 200:
        cid_list = r.json().get("IdentifierList", {}).get("CID", [])

        if cid_list:
            cid = cid_list[0]

            prop_url = (
                "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/"
                f"{cid}/property/IsomericSMILES,CanonicalSMILES,IUPACName/JSON"
            )

            pr = requests.get(prop_url, timeout=20)

            if pr.status_code == 200:
                props = pr.json().get("PropertyTable", {}).get("Properties", [])

                if props:
                    item = props[0]

                    smiles = (
                        item.get("IsomericSMILES")
                        or item.get("CanonicalSMILES")
                        or item.get("ConnectivitySMILES")
                    )

                    if smiles:
                        return smiles, item.get("IUPACName", "Unknown"), cid

    cactus_url = (
        "https://cactus.nci.nih.gov/chemical/structure/"
        f"{encoded}/smiles"
    )

    r = requests.get(cactus_url, timeout=20)

    if r.status_code == 200:
        smiles = r.text.strip()
        return smiles, "Unknown", "Unknown"

    opsin_url = f"https://opsin.ch.cam.ac.uk/opsin/{encoded}.json"
    r = requests.get(opsin_url, timeout=20)

    if r.status_code == 200:
        data = r.json()
        smiles = data.get("smiles")

        if smiles:
            return smiles, data.get("iupacName", "Unknown"), "Unknown"

    raise ValueError("找不到可用 SMILES，請改用 DDT 或更精確的英文名稱。")

smiles, iupac, cid = get_smiles(MOLECULE_NAME)

mol = Chem.MolFromSmiles(smiles)

if mol is None:
    raise ValueError("RDKit 無法解析 SMILES")

mol_h = Chem.AddHs(mol)

params = AllChem.ETKDGv3()
params.randomSeed = 2026

status = AllChem.EmbedMolecule(mol_h, params)

if status != 0:
    status = AllChem.EmbedMolecule(
        mol_h,
        randomSeed=2026,
        useRandomCoords=True
    )

try:
    AllChem.MMFFOptimizeMolecule(mol_h)
except:
    try:
        AllChem.UFFOptimizeMolecule(mol_h)
    except:
        pass

mol_block = Chem.MolToMolBlock(mol_h)

formula = rdMolDescriptors.CalcMolFormula(mol)
mw = round(Descriptors.MolWt(mol), 2)
logp = round(Crippen.MolLogP(mol), 2)
tpsa = round(rdMolDescriptors.CalcTPSA(mol), 2)
hbd = rdMolDescriptors.CalcNumHBD(mol)
hba = rdMolDescriptors.CalcNumHBA(mol)
rot = rdMolDescriptors.CalcNumRotatableBonds(mol)
rings = rdMolDescriptors.CalcNumRings(mol)
aromatic = rdMolDescriptors.CalcNumAromaticRings(mol)

functional_groups = {
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
    "Nitro": "[$([NX3](=O)=O),$([NX3+](=O)[O-])]"
}

found = []

for group_name, smarts in functional_groups.items():
    pattern = Chem.MolFromSmarts(smarts)

    if pattern and mol.HasSubstructMatch(pattern):
        found.append(group_name)

found_text = ", ".join(found) if found else "No common functional group detected"

notes = []

if "Alcohol" in found:
    notes.append("Alcohol: hydrogen bonding; oxidation / esterification possible.")
if "Aromatic ring" in found:
    notes.append("Aromatic ring: resonance and electrophilic aromatic substitution.")
if "Carboxylic acid" in found:
    notes.append("Carboxylic acid: acidic proton; resonance-stabilized conjugate base.")
if "Ester" in found:
    notes.append("Ester: hydrolysis and nucleophilic acyl substitution.")
if "Amide" in found:
    notes.append("Amide: resonance lowers nitrogen basicity.")
if "Amine" in found:
    notes.append("Amine: usually basic and nucleophilic.")
if "Alkyl halide" in found or "Aryl halide" in found:
    notes.append("Halogenated compound: useful for discussing polarity, lipophilicity, and substitution patterns.")

if not notes:
    notes.append("Inspect structure manually for reaction sites.")

notes_html = "<br>".join("- " + n for n in notes)
molblock_js = json.dumps(mol_block)

html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{MOLECULE_NAME} Flashcard</title>
<script src="https://3Dmol.org/build/3Dmol-min.js"></script>

<style>
body {{
    margin: 0;
    background: #f7f3e8;
    font-family: Arial, sans-serif;
}}

.card {{
    width: 900px;
    height: 1050px;
    margin: 30px auto;
    background: #f7f3e8;
    position: relative;
}}

h1 {{
    text-align: center;
    padding-top: 25px;
    margin-bottom: 8px;
    font-size: 34px;
}}

.subtitle {{
    text-align: center;
    font-size: 16px;
    margin-bottom: 10px;
}}

.buttons {{
    position: absolute;
    right: 65px;
    top: 95px;
}}

button {{
    width: 120px;
    height: 50px;
    margin-left: 10px;
    font-size: 14px;
    cursor: pointer;
}}

#viewer {{
    position: absolute;
    left: 70px;
    top: 160px;
    width: 760px;
    height: 560px;
    background: white;
    border: 1px solid #ddd;
}}

.info {{
    position: absolute;
    left: 60px;
    bottom: 60px;
    width: 760px;
    background: white;
    border: 1px solid gray;
    border-radius: 8px;
    padding: 18px;
    font-size: 17px;
    line-height: 1.45;
}}

.label {{
    font-weight: bold;
}}
</style>
</head>

<body>
<div class="card">

<h1>{MOLECULE_NAME.upper()}</h1>
<div class="subtitle">Organic Chemistry Teaching Flashcard</div>

<div class="buttons">
    <button onclick="showBall()">Ball-Stick</button>
    <button onclick="showVDW()">VDW</button>
</div>

<div id="viewer"></div>

<div class="info">
    <div><span class="label">Formula:</span> {formula}</div>
    <div><span class="label">Molecular Weight:</span> {mw} g/mol</div>
    <div><span class="label">MolLogP:</span> {logp} &nbsp;&nbsp; <span class="label">TPSA:</span> {tpsa}</div>
    <div><span class="label">H-bond Donor:</span> {hbd} &nbsp;&nbsp; <span class="label">H-bond Acceptor:</span> {hba}</div>
    <div><span class="label">Rotatable Bonds:</span> {rot} &nbsp;&nbsp; <span class="label">Rings:</span> {rings}</div>
    <div><span class="label">Aromatic Rings:</span> {aromatic}</div>
    <div><span class="label">PubChem CID:</span> {cid}</div>
    <div><span class="label">IUPAC:</span> {iupac}</div>
    <br>
    <div><span class="label">Functional Groups:</span> {found_text}</div>
    <br>
    <div><span class="label">Teaching Notes:</span><br>{notes_html}</div>
</div>

</div>

<script>
let molBlock = {molblock_js};
let viewer = $3Dmol.createViewer("viewer", {{backgroundColor: "white"}});

function loadModel(style) {{
    viewer.clear();
    viewer.addModel(molBlock, "mol");

    if (style === "ball") {{
        viewer.setStyle({{}}, {{
            stick: {{radius: 0.16}},
            sphere: {{scale: 0.28}}
        }});
    }}

    if (style === "vdw") {{
        viewer.setStyle({{}}, {{
            sphere: {{scale: 1.0}}
        }});
    }}

    viewer.zoomTo();
    viewer.render();
}}

function showBall() {{
    loadModel("ball");
}}

function showVDW() {{
    loadModel("vdw");
}}

showBall();
</script>

</body>
</html>
"""

output_name = MOLECULE_NAME.replace(" ", "_").replace("/", "_")
output_path = os.path.join(OUTPUT_DIR, output_name + "_flashcard.html")

with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)

print("完成！請用瀏覽器打開：")
print(os.path.abspath(output_path))
print("SMILES:", smiles)