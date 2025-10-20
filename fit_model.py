import sklearn
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import pandas as pd
from typing import List
from os.path import join

from plot_r2 import plot_r2


def load_data(target_df_path:str, feature_df_path:str, target_df_label:List[str], feature_df_label:List[str], out=False):
    target_df = pd.read_excel(target_df_path)
    feature_df = pd.read_excel(feature_df_path)
    dataset_df = pd.merge(target_df, feature_df, on='index', how='inner')

    # 过滤空值
    dataset_df = dataset_df[dataset_df[target_df_label[0]].notna()]
    if out:
        dataset_df.to_excel('dataset.xlsx')

    print(dataset_df)

    X = dataset_df[feature_df_label]
    Y = dataset_df[target_df_label]

    return X, Y


if __name__ == '__main__':

    target_df_path = join('dataset', 'merged_critic_data.xlsx')
    feature_df_path = join('dataset', 'surface_result.xlsx')
    target_df_label = ['Tc/K']
    # target_df_label = ['Pc/bar', 'Tb/K', 'Tc/K', 'Vc/cm3*mol^-1', 'omega', 'zc']
    # feature_df_label = ['Total_area_Angstrom2', 'Product_sigma_nu']

    feature_df_label = [
                        'Sphericity',
                        'Volume_Angstrom3',
                        'Density_gcm3',
                        'Min_value_kcalmol',
                        'Max_value_kcalmol',
                        'Total_area_Angstrom2',
                        'Positive_area_Angstrom2',
                        'Negative_area_Angstrom2',
                        'Average_total_kcalmol',
                        'Average_positive_kcalmol',
                        'Average_negative_kcalmol',
                        'Variance_total',
                        'Variance_positive',
                        'Variance_negative',
                        'Balance_charges_nu',
                        'Product_sigma_nu',
                        'Internal_charge_separation_kcalmol',
                        'MPI_kcalmol',
                        'Nonpolar_area_Angstrom2',
                        'Nonpolar_area_percent',
                        'Polar_area_Angstrom2',
                        'Polar_area_percent',
                        'Skewness_total',
                        'Skewness_positive',
                        'Skewness_negative',
                        ]


    X, Y = load_data(target_df_path=target_df_path, feature_df_path=feature_df_path, target_df_label=target_df_label, feature_df_label=feature_df_label, out=True)
    # ---------特征处理----------------
    # X['Product_sigma_nu'] = (X['Product_sigma_nu'] ** 0.5) #/ X['Total_area_Angstrom2']
    X['Total_area_Angstrom2'] = X['Total_area_Angstrom2'] ** 0.5
    # X['Volume_Angstrom3'] = X['Volume_Angstrom3'] ** 2
    # X['Nonpolar_area_Angstrom2'] = X['Nonpolar_area_Angstrom2'] ** 2
    # --------------------------------

    sample_idx = list(range(len(X)))
    idx_train_val, idx_test, Y_train_val, Y_test = train_test_split(
        sample_idx, Y, test_size=0.15, random_state=123  # 这样做是为了获得分割的数据集在原始数据集中的索引
    )
    idx_train, idx_val, Y_train, Y_val = train_test_split(idx_train_val, Y_train_val, test_size=0.1765, random_state=123)

    # 使用索引来获取X对应的训练/验证/测试集
    X_train = X.iloc[idx_train]
    X_val = X.iloc[idx_val]
    X_test = X.iloc[idx_test]

    # 注意更新Y_train, Y_val, 和Y_test如果它们还没有被正确赋值
    Y_train = Y.iloc[idx_train]
    Y_val = Y.iloc[idx_val]
    Y_test = Y.iloc[idx_test]

    print(f"训练集样本数: {X_train.shape[0]}, 测试集样本数: {X_test.shape[0]}")
    print(f"特征数: {X_train.shape[1]}")


    pipeline = Pipeline([
       # ('scaler', StandardScaler()),  # 第一步：数据规范化
       # ('model', LinearRegression()),
       ('model', Lasso(alpha=1, max_iter=100000))
    ])

    pipeline.fit(X_train, Y_train)

    train_pred = pipeline.predict(X_train)
    val_pred = pipeline.predict(X_val)
    test_pred = pipeline.predict(X_test)

    # 输出结果
    train_results = pd.DataFrame({
        'pre': train_pred.reshape(-1),
        'label': Y_train.to_numpy().reshape(-1),
        'idx': idx_train,
    })

    val_results = pd.DataFrame({
        'pre': val_pred.reshape(-1),
        'label': Y_val.to_numpy().reshape(-1),
        'idx': idx_val,
    })

    # 创建测试集结果DataFrame
    test_results = pd.DataFrame({
        'pre': test_pred.reshape(-1),
        'label': Y_test.to_numpy().reshape(-1),
        'idx': idx_test,
    })
    train_results.to_csv('train_result.csv')
    val_results.to_csv('val_result.csv')
    test_results.to_csv('test_result.csv')

    all_df = pd.concat([train_results, val_results, test_results], ignore_index=False)
    all_df = all_df.sort_values(by='idx', ascending=True)
    all_df.to_csv('all_result.csv')

    plot_r2(train_x_y_df_path='train_result.csv', val_x_y_df_path='val_result.csv', test_x_y_df_path='test_result.csv', save=True, save_root_path='.',
            ticks=[0, 0.5, 1.0])

    # 可选：导出模型系数
    print('模型参数')
    print(pipeline['model'].coef_)
    print(pipeline['model'].intercept_)




