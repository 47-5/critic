import pandas as pd
import numpy as np
import os
from collections import defaultdict
from typing import List


def merge_thermo_databases(input_sources, output_file="merged_thermo_database.xlsx"):
    # 步骤1: 解析输入源并读取数据
    dfs = []
    for source in input_sources:
        # 处理不同类型的输入源
        if isinstance(source, str):
            # 单个文件路径 - 读取所有工作表
            file_path = source
            xl = pd.ExcelFile(file_path)
            sheet_names = xl.sheet_names
            for sheet_name in sheet_names:
                df = xl.parse(sheet_name)
                source_name = f"{os.path.splitext(os.path.basename(file_path))[0]}_{sheet_name}"
                df['Source'] = source_name
                dfs.append(df)
            xl.close()

        elif isinstance(source, tuple) and len(source) == 2:
            # 元组格式: (文件路径, 工作表规范)
            file_path, sheet_spec = source

            # 确定要读取的工作表
            if isinstance(sheet_spec, str):
                sheet_names = [sheet_spec]
            elif isinstance(sheet_spec, list):
                sheet_names = sheet_spec
            else:
                raise ValueError(f"无效的工作表规范类型: {type(sheet_spec)}")

            xl = pd.ExcelFile(file_path)
            available_sheets = xl.sheet_names

            for sheet_name in sheet_names:
                if sheet_name not in available_sheets:
                    print(f"警告: 工作表 '{sheet_name}' 在文件 '{file_path}' 中不存在，跳过")
                    continue

                df = xl.parse(sheet_name)
                source_name = f"{os.path.splitext(os.path.basename(file_path))[0]}_{sheet_name}"
                df['Source'] = source_name
                dfs.append(df)
            xl.close()
        else:
            raise ValueError("无效的输入源格式。应为文件路径字符串或(文件路径, 工作表)元组")

    # 步骤2: 合并所有数据
    combined_df = pd.concat(dfs, ignore_index=True)

    # 检查必要列是否存在
    if 'SMILES' not in combined_df.columns:
        raise ValueError("所有数据源必须包含'SMILE'列")
    print(combined_df)

    # 步骤3: 创建数据收集字典
    data_collection = defaultdict(lambda: {
        'names': set(),
        'sources': set(),
        'properties': defaultdict(list),
        'source_data': defaultdict(dict)
    })

    # 步骤4: 按SMILES分组收集数据
    property_columns = set()
    for _, row in combined_df.iterrows():  # 遍历合并后的DataFrame中的每一行
        smiles = row['SMILES']
        record = data_collection[smiles]

        # 收集化合物名称
        if 'Compound Name' in row and pd.notna(row['Compound Name']):
            record['names'].add(str(row['Compound Name']))
        elif 'Name' in row and pd.notna(row['Name']):
            record['names'].add(str(row['Name']))
        elif 'name' in row and pd.notna(row['name']):
            record['names'].add(str(row['name']))

        # 记录来源
        source = row['Source']
        record['sources'].add(source)

        # 收集所有属性
        for col in row.index:  # 遍历当前行的所有列  # row.index返回了这一行的所有列的名字
            if col in ['SMILES', 'Compound Name', 'Name', 'Source']:
                continue

            if pd.notna(row[col]):
                property_columns.add(col)
                # 记录属性值
                record['properties'][col].append(row[col])
                # 记录来源特定数据
                record['source_data'][col][source] = row[col]

        # 步骤5: 创建合并后的数据结构
        merged_data = []

        for smiles, record in data_collection.items():
            # 创建新行
            new_row = {
                'SMILES': smiles,
                'Compound Names': '; '.join(sorted(record['names'])) if record['names'] else np.nan,
                'Sources': ', '.join(sorted(record['sources'])),
                'Source Count': len(record['sources'])
            }

            # 添加属性值（使用智能策略）
            for prop in property_columns:
                if prop not in record['properties']:
                    # 该属性在此化合物中不存在
                    continue

                values = record['properties'][prop]
                source_data = record['source_data'][prop]

                # 冲突解决策略
                if len(values) == 0:
                    # 无数据
                    new_row[prop] = np.nan
                    new_row[f'{prop}_Sources'] = np.nan

                elif len(values) == 1:
                    # 单一来源
                    new_row[prop] = values[0]
                    new_row[f'{prop}_Sources'] = list(source_data.keys())[0]

                else:
                    # 多来源 - 智能处理
                    unique_vals = set(values)

                    if len(unique_vals) == 1:
                        # 所有来源值相同
                        new_row[prop] = values[0]
                        new_row[f'{prop}_Sources'] = '; '.join(source_data.keys())
                    else:
                        # 值不同 - 根据属性类型处理
                        if prop.lower().startswith(('critical', 'temperature', 'pressure', 'acentric', 'factor')):
                            # 数值属性：计算平均值
                            try:
                                num_vals = [float(v) for v in values]
                                new_row[prop] = np.mean(num_vals)
                                new_row[f'{prop}_Conflicts'] = f"{len(values)} values (avg: {new_row[prop]:.4f})"
                            except:
                                # 如果转换失败，取第一个值
                                new_row[prop] = values[0]
                                new_row[f'{prop}_Conflicts'] = f"{len(values)} values (first used)"
                        else:
                            # 非数值属性：取第一个值
                            new_row[prop] = values[0]
                            new_row[f'{prop}_Conflicts'] = f"{len(values)} values (first used)"

                        # 记录来源详细数据
                        source_details = [f"{src}: {val}" for src, val in source_data.items()]
                        new_row[f'{prop}_Sources'] = '; '.join(source_details)

            merged_data.append(new_row)

        # 步骤6: 创建最终DataFrame
        merged_df = pd.DataFrame(merged_data)

        # 排序列：核心列 + 属性列 + 来源列 + 冲突列
        core_columns = ['SMILES', 'Compound Names', 'Sources', 'Source Count']
        prop_columns = sorted([col for col in merged_df.columns if
                               col not in core_columns and not col.endswith(('_Sources', '_Conflicts'))])

        # 组织列顺序
        ordered_columns = core_columns.copy()
        for prop in prop_columns:
            ordered_columns.append(prop)
            if f'{prop}_Conflicts' in merged_df.columns:
                ordered_columns.append(f'{prop}_Conflicts')
            ordered_columns.append(f'{prop}_Sources')

        # 确保只包含实际存在的列
        final_columns = [col for col in ordered_columns if col in merged_df.columns]
        merged_df = merged_df[final_columns]

        # 步骤7: 保存结果
        merged_df.to_excel(output_file, index=False)
        print(f"成功合并数据库! 共处理 {len(dfs)} 个数据表, 得到 {len(merged_df)} 个唯一化合物。")
        print(f"结果已保存至: {output_file}")

    return merged_df

if __name__ == '__main__':


    input_source = [
        ('critic_data.xlsx', ['Sheet1', 'Sheet2', 'Sheet3', 'Sheet4', 'Sheet5'])
    ]
    merge_thermo_databases(input_sources=input_source, output_file='merged_thermo_database.xlsx')
