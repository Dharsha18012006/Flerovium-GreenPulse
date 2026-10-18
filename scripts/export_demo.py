"""Export first test image per class for a reproducible, clearly attributed demo."""
import json
from pathlib import Path
import shutil

release=Path(__file__).resolve().parent.parent
rows=json.loads((release/'artifacts/combined-split.json').read_text())
out=release/'artifacts/demo-leaves';out.mkdir(exist_ok=False)
for label in ['early_blight','healthy','late_blight']:
    row=next(r for r in rows if r['split']=='test' and r['label']==label)
    shutil.copyfile(release.parent/row['path'],out/(label+'.jpg'))
(out/'ATTRIBUTION.md').write_text('PlantVillage RGB dataset: Mohanty, Hughes and Salathe (2016), https://doi.org/10.3389/fpls.2016.01419 . Original repository https://github.com/spMohanty/PlantVillage-Dataset . CC BY-SA 3.0 per author dataset card: https://huggingface.co/datasets/mohanty/PlantVillage . License: https://creativecommons.org/licenses/by-sa/3.0/ . Files are unchanged original photographs, renamed by class. First test image per class, not cherry-picked. These are dataset examples, not real user reports.\n')
print(out)
