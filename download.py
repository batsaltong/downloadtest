import re
import os
import streamlit as st
from pytubefix import YouTube
from pytubefix.cli import on_progress

# 영상이 저장될 디렉토리 설정 (서버 하위의 폴더로 사용)
DOWNLOAD_DIR = "downloaded_videos"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def sanitize_filename(filename):
    # Windows에서 사용 불가능한 문자 제거: \ / * ? : " < > |
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def get_youtube_video_id(url):
    # URL에서 유튜브 영상 ID 추출 (youtu.be/ID 또는 youtube.com/watch?v=ID)
    regex_patterns = [
        r"(?:https?:\/\/)?(?:www\.)?youtu\.be\/([\w\-]{11})",
        r"(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([\w\-]{11})"
    ]
    for pattern in regex_patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def download_video_to_bytes(url):
    # 유효한 URL 확인을 위해 영상 ID 추출
    video_id = get_youtube_video_id(url)
    if not video_id:
        st.error("유효한 유튜브 URL이 아닙니다.")
        return None, None

    try:
        # pytubefix를 이용한 YouTube 객체 생성 (진행률 콜백 포함)
        yt = YouTube(url, on_progress_callback=on_progress)
        st.write("영상 제목:", yt.title)
        stream = yt.streams.get_highest_resolution()
        if stream is None:
            st.error("다운로드 가능한 스트림을 찾을 수 없습니다.")
            return None, None

        # 영상 제목에서 파일명을 생성하고 sanitize_filename 함수를 통해 정리
        raw_file_name = f"{yt.title}.mp4"
        file_name = sanitize_filename(raw_file_name)
        file_path = os.path.join(DOWNLOAD_DIR, file_name)

        # 지정한 DOWNLOAD_DIR에 영상 파일 다운로드
        stream.download(output_path=DOWNLOAD_DIR, filename=file_name)

        # 저장된 파일을 바이너리 모드로 읽어 반환
        with open(file_path, "rb") as file:
            video_bytes = file.read()

        return video_bytes, file_name
    except Exception as e:
        st.error(f"에러 발생: {e}")
        return None, None

st.title("pytubefix를 활용한 유튜브 영상 다운로드 (서버 저장)")

# 유튜브 URL 입력 및 다운로드 버튼
video_url = st.text_input("유튜브 영상 URL을 입력하세요:")
if video_url and st.button("영상 다운로드"):
    video_bytes, filename = download_video_to_bytes(video_url)
    if video_bytes is not None:
        st.download_button(
            label="다운로드 영상 파일",
            data=video_bytes,
            file_name=filename,
            mime="video/mp4"
        )

st.write("--------------------------------------------------------")
st.header("서버에 저장된 영상 목록")

# 저장된 영상 목록 확인 및 선택
videos = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith(".mp4")]
if videos:
    selected_video = st.selectbox("영상 선택", videos)
    if st.button("선택한 영상 보기"):
        file_path = os.path.join(DOWNLOAD_DIR, selected_video)
        try:
            # 저장된 영상을 읽어 st.video로 출력
            with open(file_path, "rb") as f:
                video_bytes = f.read()
            st.video(video_bytes)
        except Exception as e:
            st.error(f"영상을 불러오는 데 실패했습니다: {e}")
else:
    st.info("저장된 영상이 없습니다.")