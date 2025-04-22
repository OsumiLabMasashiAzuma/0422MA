import streamlit as st
import subprocess

def convert_full_video(input_file, output_file, ffmpeg_path):
    try:
        subprocess.run([
            ffmpeg_path, '-i', input_file, '-c:v', 'copy', '-c:a', 'copy', output_file
        ], check=True)
        st.success(f"✅ 変換が完了しました: {output_file}")
    except FileNotFoundError as e:
        st.error(f"❌ 指定されたファイルが見つかりません: {e}")
    except subprocess.CalledProcessError as e:
        st.error(f"❌ FFmpegの変換中にエラーが発生しました: {e}")

# === StreamlitでGUI作成 ===
st.title("🎥 フル動画変換ツール")

# 入力フォーム
input_file = st.text_input("入力ファイルパスを指定してください", value=r"C:\Users\kinki\Downloads\sample_input.dav")
output_file = st.text_input("出力ファイルパスを指定してください", value=r"C:\Users\kinki\Downloads\output.mp4")
ffmpeg_path = st.text_input("ffmpeg.exe のフルパスを指定してください", value=r"C:\Users\kinki\Downloads\ffmpeg-xxx\bin\ffmpeg.exe")

# 実行ボタン
if st.button("変換開始！"):
    convert_full_video(input_file, output_file, ffmpeg_path)
