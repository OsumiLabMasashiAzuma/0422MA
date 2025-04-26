import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.stats import ttest_ind
import os

# === タイトル ===
st.title('Activity Comparison Between Groups GUI')

# === ファイルアップロード ===
st.header('1. ファイル選択')
cage1_file = st.file_uploader('Cage1ファイルを選択', type=['xlsx'])
cage2_file = st.file_uploader('Cage2ファイルを選択', type=['xlsx'])

# === 出力フォルダ指定 ===
st.header('2. 出力フォルダ指定')
output_folder = st.text_input('保存先フォルダを指定', value='output_images')
os.makedirs(output_folder, exist_ok=True)

# === 分割タイミング入力 ===
st.header('3. 分割時間指定')
split_times_text = st.text_input('分割したい時刻をカンマ区切りで入力 (例: 2025-03-09 00:00)', '')

# === 実行ボタン ===
if st.button('グラフ作成実行'):
    if cage1_file is None or cage2_file is None:
        st.error('両方のファイルをアップロードしてください')
    else:
        # === データ読み込み ===
        df_cage1 = pd.read_excel(cage1_file)
        df_cage2 = pd.read_excel(cage2_file)

        df_cage1['Hour'] = pd.to_datetime(df_cage1['Hour'])
        df_cage2['Hour'] = pd.to_datetime(df_cage2['Hour'])

        df_cage1['Group'] = 'Cage1'
        df_cage2['Group'] = 'Cage2'

        df_all = pd.concat([df_cage1, df_cage2], ignore_index=True)
        df_all['Hour'] = df_all['Hour'].dt.floor('min')  # ミリ秒のズレを防ぐ

        # === 平均 ± SEM 集計 ===
        summary = df_all.groupby(['Group', 'Hour'])['Total_Distance'].agg(mean='mean', sem='sem').reset_index()
        summary['Hour'] = summary['Hour'].dt.floor('min')

        # === 分割タイミング設定 ===
        if split_times_text.strip():
            split_times = [pd.to_datetime(t.strip()).floor('min') for t in split_times_text.split(',')]
        else:
            split_times = []

        all_hours = sorted(df_all['Hour'].unique())
        start_time = all_hours[0]
        end_time = all_hours[-1]
        cut_points = [start_time] + split_times + [end_time]

        st.write("⏱ データ範囲:", start_time, "～", end_time)
        st.write("📌 分割ポイント:", cut_points)

        created_images = []

        # === 区間ごとにグラフ作成 ===
        for i in range(len(cut_points) - 1):
            t_start, t_end = cut_points[i], cut_points[i + 1]
            df_interval = df_all[(df_all['Hour'] >= t_start) & (df_all['Hour'] < t_end)]
            summary_interval = summary[(summary['Hour'] >= t_start) & (summary['Hour'] < t_end)]

            st.write(f"▶ 区間 {i+1}: {t_start} ～ {t_end} → df_interval: {len(df_interval)} 行")

            if df_interval.empty or summary_interval.empty:
                st.warning(f"⚠ 区間 {t_start} ～ {t_end} に有効なデータがありません。スキップします。")
                continue

            # --- グラフ描画 ---
            fig, ax = plt.subplots(figsize=(14, 6))
            group_colors = {}

            for group, data in summary_interval.groupby('Group'):
                line, = ax.plot(data['Hour'], data['mean'], label=group)
                ax.fill_between(data['Hour'], data['mean'] - data['sem'], data['mean'] + data['sem'], alpha=0.3, color=line.get_color())
                group_colors[group] = line.get_color()

            # --- 有意差マーカー ---
            markers = []
            for hour in sorted(df_interval['Hour'].unique()):
                g1 = df_interval[(df_interval['Group'] == 'Cage1') & (df_interval['Hour'] == hour)]['Total_Distance']
                g2 = df_interval[(df_interval['Group'] == 'Cage2') & (df_interval['Hour'] == hour)]['Total_Distance']
                if len(g1) > 1 and len(g2) > 1:
                    stat, p = ttest_ind(g1, g2, equal_var=False)
                    if p < 0.001:
                        star = '***'
                    elif p < 0.01:
                        star = '**'
                    elif p < 0.05:
                        star = '*'
                    else:
                        star = ''
                else:
                    star = ''
                if star:
                    means = summary_interval[summary_interval['Hour'] == hour].set_index('Group')['mean']
                    top_group = means.idxmax()
                    max_mean = means.max()
                    markers.append((hour, max_mean + 20, star, group_colors[top_group]))

            for hour, y_pos, star, color in markers:
                ax.text(hour, y_pos, star, ha='center', va='bottom', fontsize=14, color=color)

            ax.set_xlabel("Hour")
            ax.set_ylabel("Total Distance (Mean ± SEM)")
            ax.set_title(f"Activity Comparison: {t_start.strftime('%m-%d %H:%M')} to {t_end.strftime('%m-%d %H:%M')}")
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.grid(True)
            plt.legend()

            # --- 保存 ---
            filename = f"group_comparison_{t_start.strftime('%m%d_%H%M')}_to_{t_end.strftime('%m%d_%H%M')}.png"
            save_path = os.path.join(output_folder, filename)
            fig.savefig(save_path, dpi=300)
            created_images.append(save_path)
            plt.close()

        st.success(f"{len(created_images)} 枚の画像を作成しました！")

        # === 作成した画像を表示 ===
        st.header('4. 作成されたグラフ一覧')
        for img_path in created_images:
            st.image(img_path, caption=os.path.basename(img_path), use_column_width=True)