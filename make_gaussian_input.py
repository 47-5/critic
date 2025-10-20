import ase
from ase.io import read, write
import os
import glob


def structure_file_to_gjf(structure_file_path, gjf_path=None, nproc='12', mem='12GB', chk_path=None,
                   gaussian_keywords=None, charge_and_multiplicity=None,
                   add_other_tasks=False, other_tasks:list=None):
    # default path of chk and gjf
    structure_file_name = structure_file_path.split('.')[0]
    if chk_path is None:
        chk_path = '{}.chk'.format(structure_file_name)
    if gjf_path is None:
        gjf_path = '{}.gjf'.format(structure_file_name)
    assert ('(' not in gjf_path) and (')' not in gjf_path), \
        'gaussian dose not allow ( or ) in the name of .gjf and .chk files'
    assert ('(' not in chk_path) and (')' not in chk_path), \
        'gaussian dose not allow ( or ) in the name of .gjf and .chk files'
    # default task
    if gaussian_keywords is None:
        gaussian_keywords = '#p opt freq b3lyp/6-31g*'
    # default charge and multiplicity
    if charge_and_multiplicity is None:
        charge_and_multiplicity = f'0 1'
    # default other tasks
    if other_tasks is None:
        other_tasks = [
            '#p m062x/def2tzvp geom=check',
            '#p m062x/def2tzvp scrf=solvent=water geom=check',
        ]

    try:
        if os.path.exists(gjf_path):
            os.remove(gjf_path)
        write_gjf_link0_and_keyword(gjf_path=gjf_path, chk_path=chk_path, nproc=nproc, mem=mem,
                                         gaussian_keywords=gaussian_keywords,
                                         charge_and_multiplicity=charge_and_multiplicity, note=structure_file_name)
        write_gjf_coord(gjf_path=gjf_path, structure_file_path=structure_file_path)
        if add_other_tasks:
            for task_index, task in enumerate(other_tasks):
                i_chk_path = chk_path.split('.')[0] + f'_{task_index + 1}' + '.chk'
                write_gjf_link0_and_keyword(gjf_path=gjf_path, chk_path=i_chk_path, nproc=nproc, mem=mem,
                                                 gaussian_keywords=task, charge_and_multiplicity=charge_and_multiplicity,
                                                 note=structure_file_name, old_chk_path=chk_path, add_link1=True)
                write_gjf_blank_line(gjf_path=gjf_path, blank_line_number=2)
        return True
    except:
        print(f'Error! There is something wrong when converting {structure_file_path} to gjf file, please check it.')
        return False


def write_gjf_link0_and_keyword(gjf_path, chk_path, nproc, mem, gaussian_keywords, charge_and_multiplicity, note,
                                old_chk_path=None, add_link1=False):
    with open(gjf_path, 'a') as gjf:
        if add_link1:
            gjf.write('--link1--' + '\n')
        gjf.write(f'%nproc={nproc}' + '\n')
        gjf.write(f'%mem={mem}' + '\n')
        if old_chk_path is not None:
            gjf.write(f'%oldchk={old_chk_path}' + '\n')
        gjf.write(f'%chk={chk_path}' + '\n')
        gjf.write(f'{gaussian_keywords}' + '\n')
        gjf.write('\n')
        gjf.write(f'{note}' + '\n')
        gjf.write('\n')
        gjf.write(f'{charge_and_multiplicity}' + '\n')
        gjf.close()
    return None


def write_gjf_coord(gjf_path, structure_file_path):
    atoms = read(structure_file_path)
    pos = atoms.positions
    # number = atoms.numbers
    chemical_symbols = atoms.get_chemical_symbols()
    with open(gjf_path, 'a') as gjf:
        for chemical_symbols, xyz in zip(chemical_symbols, pos):
            x, y, z = xyz[0], xyz[1], xyz[2]
            gjf.write(f'{chemical_symbols} {x} {y} {z}' + '\n')
        gjf.write('\n\n')
    return None


def write_gjf_blank_line(gjf_path, blank_line_number=1):
    with open(gjf_path, 'a') as gjf:
        gjf.write('\n' * blank_line_number)
    return None


if __name__ == '__main__':

    mode = 'batch'

    nproc = '128'
    mem = '512GB'
    chk_path = None
    gaussian_keywords = '# opt freq b3lyp/6-31g(d,p) em=gd3bj'
    charge_and_multiplicity = '0 1'
    add_other_tasks = True
    other_tasks = [
            '#p m062x/def2tzvp geom=check',
            '#p m062x/def2tzvp scrf=solvent=water geom=check',
        ]

    if mode == 'single':
        structure_file_path = '01.mol'
        gjf_path = '01.gjf'
        structure_file_to_gjf(structure_file_path=structure_file_path, gjf_path=gjf_path, nproc=nproc, mem=mem,
                              chk_path=chk_path, gaussian_keywords=gaussian_keywords,
                              charge_and_multiplicity=charge_and_multiplicity, add_other_tasks=add_other_tasks,
                              other_tasks=other_tasks)

    elif mode == 'batch':

        # structure_file_name_list = [f'{str(i).zfill(2)}.mol' for i in range(1, 44)]
        structure_file_name_list = glob.glob('*.mol')
        print(structure_file_name_list)
        for i in structure_file_name_list:
            structure_file_to_gjf(structure_file_path=i, gjf_path=None, nproc=nproc, mem=mem,
                                  chk_path=chk_path, gaussian_keywords=gaussian_keywords,
                                  charge_and_multiplicity=charge_and_multiplicity, add_other_tasks=add_other_tasks,
                                  other_tasks=other_tasks)

