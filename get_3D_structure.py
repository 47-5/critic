import pubchempy as pcp
from openbabel import pybel
from rdkit import Chem
from rdkit.Chem import AllChem
import pandas as pd


def fetch_3d_from_pubchem(smiles, out_file_path, output_format="mol"):
    try:
        # 通过SMILES查询PubChem，获取首个匹配的CID
        compounds = pcp.get_compounds(smiles, namespace="smiles")
        if not compounds:
            return None
        cid = compounds[0].cid

        # 下载3D Conformer数据（SDF格式）
        sdf_data = pcp.download("SDF", f"pubchem_3d_{cid}.sdf", cid, record_type="3d", overwrite=True)

        # 转换为目标格式（如mol）
        mol = next(pybel.readfile("sdf", f"pubchem_3d_{cid}.sdf"))
        mol.write(output_format, out_file_path)
        return True

    except Exception as e:
        print(f"PubChem下载失败: {e}, SMILES: {smiles}")
        return False


def generate_3d_with_openbabel(smiles, out_file_path, output_format="mol"):
    try:
        # 将SMILES转换为分子对象
        mol = pybel.readstring("smi", smiles)

        # 生成3D坐标（默认使用MMFF94力场）
        mol.make3D(forcefield="mmff94", steps=500)  # 增加优化步数

        # 局部能量最小化
        mol.localopt(forcefield="mmff94", steps=1000)

        # 保存为指定格式
        mol.write(output_format, out_file_path)
        return True

    except Exception as e:
        print(f"OpenBabel生成失败: {e}, SMILES: {smiles}")
        return False


def generate_3d_with_rdkit(smiles, out_file_path, output_format="mol", rdkit_sdf_name='temp.sdf'):
    try:
        # 读取SMILES并解析立体化学
        mol = Chem.MolFromSmiles(smiles)
        mol = Chem.AddHs(mol)  # 添加氢原子

        # 生成3D构象（ETKDGv3算法）
        params = AllChem.ETKDGv3()
        params.randomSeed = 42  # 可复现结果
        status = AllChem.EmbedMolecule(mol, params)

        if status == -1:
            raise RuntimeError("rdkit构象生成失败")

        # 力场优化（UFF或MMFF）
        AllChem.MMFFOptimizeMolecule(mol, mmffVariant="MMFF94s")

        # 保存为SDF（含3D坐标）
        writer = Chem.SDWriter(rdkit_sdf_name)
        writer.write(mol)
        writer.close()
        mol = next(pybel.readfile("sdf", filename=rdkit_sdf_name))
        mol.write(output_format, out_file_path)
        return True

    except Exception as e:
        print(f"RDKit生成失败: {e}, SMILES: {smiles}")
        return False


def get_3D_structure_form_smiles(smiles, out_file_path, output_format="mol", rdkit_sdf_name='temp.sdf'):
    if fetch_3d_from_pubchem(smiles=smiles, out_file_path=out_file_path, output_format=output_format):
        return True
    elif generate_3d_with_rdkit(smiles=smiles, out_file_path=out_file_path, output_format=output_format, rdkit_sdf_name=rdkit_sdf_name):
        return True
    elif generate_3d_with_openbabel(smiles=smiles, out_file_path=out_file_path, output_format=output_format):
        return True
    else:
        return False


def convert_file_format(in_format, in_path, out_format, out_path):
    mol = next(pybel.readfile(format=in_format, filename=in_path))
    mol.write(format=out_format, filename=out_path)
    return None


if __name__ == '__main__':
    # 示例调用
    run_mode = 'batch'

    if run_mode == 'single':
        smiles = "F/C=C/F"  # 反式二氟乙烯（含立体化学）
        fetch_3d_from_pubchem(smiles, out_file_path='test.mol')

    elif run_mode == 'batch':

        df = pd.read_excel('merged_critic_data.xlsx')
        smiles_list = df['SMILES']
        index_list = df['index']
        success = []
        fail = []
        for index, smiles in zip(index_list, smiles_list):
            #flag = fetch_3d_from_pubchem(smiles=smiles, out_file_path=f'structure_3D/{index}.mol', output_format='mol')
            flag = get_3D_structure_form_smiles(smiles=smiles, out_file_path=f'structure_3D/{index}.mol', output_format='mol', rdkit_sdf_name=f'{index}_temp.sdf')
            if flag:
                success.append(smiles)
            else:
                fail.append(smiles)
        with open('success.txt', 'w') as f:
            for i in success:
                f.write(i + '\n')
        with open('fail.txt', 'w') as f:
            for i in fail:
                f.write(i + '\n')

    elif run_mode == 'convert':
        in_format='sdf'
        in_path='Conformer3D_COMPOUND_CID_356.sdf'
        out_format='mol'
        out_path='22.mol'
        convert_file_format(in_format, in_path, out_format, out_path)