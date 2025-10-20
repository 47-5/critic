import pandas as pd
import re
import os


def extract_prediction_data(input_file_path, output_dir):
    """
    从预测数据文件中提取不同维度的预测结果，并保存为独立的Excel文件

    参数:
    input_file_path (str): 原始数据文件路径
    output_dir (str): 输出Excel文件的目录路径

    返回:
    list: 生成的Excel文件路径列表
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 读取输入文件内容
    with open(input_file_path, 'r') as f:
        data = f.read()

    # 分割不同维度的数据块
    blocks = re.split(r'Predictions \(y,pred,y-pred\) by the model of dimension:\s+', data)[1:]

    output_files = []

    for block in blocks:
        # 提取维度号和实际数据
        lines = block.strip().split('\n')
        if not lines:
            continue

        dim_line = lines[0]
        dim = dim_line.split()[0]

        # 移除最后的RMSE行
        data_lines = [line.strip() for line in lines[1:]
                      if line.strip() and not line.startswith('Prediction RMSE and MaxAE')]

        # 解析数据
        records = []
        for line in data_lines:
            # 分割数据行
            values = line.split()
            if len(values) >= 3:
                try:
                    records.append({
                        'label': float(values[0]),
                        'pre': float(values[1]),
                        'delta': float(values[2])
                    })
                except ValueError:
                    # 忽略无法解析的行
                    continue

        # 创建DataFrame并保存为Excel
        if records:
            df = pd.DataFrame(records)
            filename = f'dimension_{dim}.xlsx'
            output_path = os.path.join(output_dir, filename)
            df.to_excel(output_path, index=False)
            output_files.append(output_path)
            print(f'已创建文件: {output_path} (维度 {dim}, {len(df)} 行数据)')
        else:
            print(f'警告: 维度 {dim} 未找到有效数据')

    return output_files


# 使用示例
if __name__ == "__main__":
    input_file = "predict_Y.out"  # 替换为实际输入文件路径
    output_directory = 'test'  # 替换为实际输出目录路径

    created_files = extract_prediction_data(input_file, output_directory)
    print(f"\n已创建 {len(created_files)} 个文件:")
    for file in created_files:
        print(f" - {file}")