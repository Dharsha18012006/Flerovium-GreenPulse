"""Plot recorded real metrics without model evaluation or fabricated observations."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--results',type=Path,required=True);a=p.parse_args()
    metrics=json.loads((a.results/'metrics.json').read_text());matrix=np.array(metrics['confusion_matrix'])
    labels=[label.replace('_',' ').title() for label in metrics['labels']]
    fig,ax=plt.subplots(figsize=(6,5),layout='constrained');ax.imshow(matrix,cmap='Greens',vmin=0,vmax=matrix.max())
    ax.set(xticks=range(3),yticks=range(3),xticklabels=labels,yticklabels=labels,xlabel='Predicted class',ylabel='True class',title='GreenPulse · frozen LinuxONE classifier\n54 held-out PlantVillage leaves')
    for i in range(3):
        for j in range(3):ax.text(j,i,str(matrix[i,j]),ha='center',va='center',color='white' if matrix[i,j]>matrix.max()/2 else 'black',fontsize=16)
    fig.savefig(a.results/'confusion_matrix.png',dpi=170)
    plt.close(fig)
