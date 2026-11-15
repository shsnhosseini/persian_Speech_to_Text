import os
import tempfile
from dotenv import load_dotenv
from google import genai
from google.genai import types
import streamlit as st

load_dotenv()

AUDIO_MIME_TYPES = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
}

st.set_page_config(
    page_title="تبدیل گفتار به متن فارسی",
    page_icon="\U0001F3A4",
    layout="centered",
)

# Custom CSS for RTL and Persian font
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        direction: rtl;
        font-family: 'Vazirmatn', 'Tahoma', 'Arial', sans-serif;
        text-align: right;
    }

    .stApp {
        direction: rtl;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Vazirmatn', sans-serif;
        text-align: right;
        direction: rtl;
    }

    h1 {
        text-align: center;
    }

    h3 {
        font-size: 1rem;
        font-weight: 600;
    }

    h2 {
        font-size: 0.7rem;
        font-weight: 600;
        margin: 0;
    }

    p, div, span, label, button {
        font-family: 'Vazirmatn', sans-serif;
        text-align: right;
        direction: rtl;
    }

    .stTextArea textarea, .stTextInput input {
        direction: rtl;
        text-align: right;
    }

    .stAudio {
        text-align: right;
    }

    .stButton button {
        direction: rtl;
        text-align: right;
    }

    .transcription-box {
        background: #f5f7f9;
        border: 1px solid #e1e4e8;
        border-radius: 8px;
        padding: 4px 16px 8px;
        text-align: right;
        direction: rtl;
        font-size: 1rem;
        line-height: 1.8;
        white-space: pre-wrap;
    }

    .transcription-text {
        display: block;
        text-align: justify;
        unicode-bidi: embed;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("\U0001F3A4 تبدیل گفتار به متن فارسی")
st.caption("یک فایل صوتی بارگذاری کنید تا متن فارسی آن استخراج شود.")

client = genai.Client()

uploaded_file = st.file_uploader("انتخاب فایل صوتی", type=["mp3", "wav", "m4a", "ogg", "flac"])

if uploaded_file is not None:
    st.audio(uploaded_file)

    if st.button("تبدیل به متن فارسی"):
        with st.spinner("در حال بارگذاری و تبدیل..."):
            # Keep the original extension when writing the temporary audio file.
            suffix = os.path.splitext(uploaded_file.name)[1]
            mime_type = AUDIO_MIME_TYPES.get(suffix.lower())
            tmp_path = os.path.join(tempfile.gettempdir(), f"stt_upload{suffix}")
            with open(tmp_path, "wb") as tmp:
                tmp.write(uploaded_file.getvalue())

            try:
                if mime_type is None:
                    raise ValueError(f"Unsupported audio file extension: {suffix or '(none)'}")

                uploaded_speech = client.files.upload(
                    file=tmp_path,
                    config=types.UploadFileConfig(mime_type=mime_type),
                )
                
                # Transcribe the uploaded audio to Persian text using the Gemini model
                response = client.models.generate_content(
                    model="gemini-3.5-transcribe",
                    contents=["Transcribe this audio to persian text", uploaded_speech],
                )

                transcription = None
                for part in response.candidates[0].content.parts:
                    t = getattr(part, "audio_transcription", None)
                    if t is not None:
                        transcription = t.text
                        break

                if transcription:
                    st.success("تبدیل با موفقیت انجام شد")
                    st.subheader("متن استخراج شده")
                    st.markdown(
                        f'<div class="transcription-box"><span class="transcription-text">{transcription}</span></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.error("متنی در پاسخ یافت نشد.")

            except Exception as exc:
                st.error(f"خطا: {exc}")
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
