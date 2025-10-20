import re
import glob
import pandas as pd
import os


def extract_multiwfn_info(filename):
    results = {}

    with open(filename, 'r') as file:
        content = file.read()

        # 提取Isosurface area和Sphericity
        isosurface_match = re.search(r"Isosurface area:\s*[\d.]+\s+Bohr\^2\s+\(\s*([\d.]+)\s+Angstrom\^2\)", content)
        sphericity_match = re.search(r"Sphericity:\s*([\d.]+)", content)

        if isosurface_match:
            results['Isosurface_area_Angstrom2'] = float(isosurface_match.group(1))
        if sphericity_match:
            results['Sphericity'] = float(sphericity_match.group(1))

        # 提取Summary of surface analysis部分
        summary_section = re.search(r"=\s*Summary of surface analysis\s*=(.*?)Surface analysis finished!", content,
                                    re.DOTALL)

        if summary_section:
            summary = summary_section.group(1)

            # 定义要提取的字段及其正则表达式模式
            patterns = {
                'Volume_Bohr3': r"Volume:\s*([\d.]+)\s+Bohr\^3",
                'Volume_Angstrom3': r"Volume:\s*[\d.]+\s+Bohr\^3\s+\(\s*([\d.]+)\s+Angstrom\^3\)",
                'Density_gcm3': r"Estimated density.*?:\s*([\d.]+)\s+g/cm\^3",
                'Min_value_kcalmol': r"Minimal value:\s*([-\d.]+)\s+kcal/mol",
                'Max_value_kcalmol': r"Maximal value:\s*([-\d.]+)\s+kcal/mol",
                'Total_area_Angstrom2': r"Overall surface area:.*?\(\s*([\d.]+)\s+Angstrom\^2\)",
                'Positive_area_Angstrom2': r"Positive surface area:.*?\(\s*([\d.]+)\s+Angstrom\^2\)",
                'Negative_area_Angstrom2': r"Negative surface area:.*?\(\s*([\d.]+)\s+Angstrom\^2\)",
                'Average_total_kcalmol': r"Overall average value:.*?\(\s*([-\d.]+)\s+kcal/mol\)",
                'Average_positive_kcalmol': r"Positive average value:.*?\(\s*([-\d.]+)\s+kcal/mol\)",
                'Average_negative_kcalmol': r"Negative average value:.*?\(\s*([-\d.]+)\s+kcal/mol\)",
                'Variance_total': r"Overall variance.*?:\s*[\d.]+\s+a\.u\.\^2\s+\(\s*([\d.]+)\s+\(kcal/mol\)\^2\)",
                'Variance_positive': r"Positive variance:.*?\(\s*([\d.]+)\s+\(kcal/mol\)\^2\)",
                'Variance_negative': r"Negative variance:.*?\(\s*([\d.]+)\s+\(kcal/mol\)\^2\)",
                'Balance_charges_nu': r"Balance of charges \(nu\):\s*([\d.]+)",
                'Product_sigma_nu': r"Product of sigma\^2_tot and nu:.*?\(\s*([\d.]+)\s+\(kcal/mol\)\^2\)",
                'Internal_charge_separation_kcalmol': r"Internal charge separation \(Pi\):.*?\(\s*([-\d.]+)\s+kcal/mol\)",
                'MPI_kcalmol': r"Molecular polarity index \(MPI\):.*?\(\s*([-\d.]+)\s+kcal/mol\)",
                'Nonpolar_area_Angstrom2': r"Nonpolar surface area.*?:\s*([\d.]+)\s+Angstrom\^2",
                'Nonpolar_area_percent': r"Nonpolar surface area.*?\(\s*([\d.]+)\s+%\)",
                'Polar_area_Angstrom2': r"Polar surface area.*?:\s*([\d.]+)\s+Angstrom\^2",
                'Polar_area_percent': r"Polar surface area.*?\(\s*([\d.]+)\s+%\)",
                'Skewness_total': r"Overall skewness:\s*([-\d.]+)",
                'Skewness_positive': r"Positive skewness:\s*([-\d.]+)",
                'Skewness_negative': r"Negative skewness:\s*([-\d.]+)"
            }

            for key, pattern in patterns.items():
                match = re.search(pattern, summary)
                if match:
                    # 尝试转换为浮点数（百分比除外）
                    if 'percent' not in key:
                        try:
                            results[key] = float(match.group(1))
                        except ValueError:
                            results[key] = match.group(1)
                    else:
                        results[key] = match.group(1)

    return results


if __name__ == "__main__":
    # filename = "0.sufrace_out"  # 替换为实际文件名
    # results = extract_multiwfn_info(filename)
    #
    # # 打印提取结果
    # for key, value in results.items():
    #     print(f"{key}: {value}")
    # print(results)
    filename_list = [f'{i}.sufrace_out' for i in range(584)]
    surface_results = []
    for index, file in enumerate(filename_list):
        filepath = os.path.join('surface_result', file)
        result = extract_multiwfn_info(filename=filepath)
        result['index'] = index
        surface_results.append(result)

    df = pd.DataFrame(data=surface_results)
    print(df)
    df.to_excel('surface_result.xlsx')
