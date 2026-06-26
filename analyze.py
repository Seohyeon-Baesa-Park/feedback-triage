import os
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

matplotlib.use('Agg')

HERE = os.path.dirname(os.path.abspath(__file__))

KEYWORDS = {
    '불만': ['오류', '느려', '불편', '안돼', '문제', '달아', '별로', '이상'],
    '요청': ['있으면', '원해요', '해주세요', '추가', '개선'],
    '칭찬': ['좋아요', '친절', '깨끗', '맛있', '최고'],
    '문의': ['언제', '어떻게', '되나요', '알려'],
}
TYPE_ORDER = ['불만', '요청', '칭찬', '문의', '기타']
TYPE_EMOJI = {'불만': '😡', '요청': '🙋', '칭찬': '😊', '문의': '❓', '기타': '📝'}
TYPE_COLOR = {
    '불만': '#FF4B4B',
    '요청': '#F5A623',
    '칭찬': '#21C55D',
    '문의': '#3B82F6',
    '기타': '#9CA3AF',
}


def read_csv(filepath: str) -> pd.DataFrame:
    for enc in ('utf-8-sig', 'utf-8', 'cp949', 'euc-kr'):
        try:
            return pd.read_csv(filepath, encoding=enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise ValueError(f"{filepath} 을 읽을 수 있는 인코딩을 찾지 못했습니다.")


def classify(text: str) -> str:
    if not isinstance(text, str):
        return '기타'
    for label, kws in KEYWORDS.items():
        if any(kw in text for kw in kws):
            return label
    return '기타'


# ── 데이터 로드 ──────────────────────────────────────────────
@st.cache_data
def load_data() -> pd.DataFrame:
    df = read_csv(os.path.join(HERE, 'feedback.csv'))
    df['별점'] = pd.to_numeric(df['별점'], errors='coerce')
    df['유형'] = df['내용'].apply(classify)
    return df


# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(page_title='피드백 대시보드', page_icon='💬', layout='wide')
st.title('💬 고객 피드백 분석 대시보드')

df = load_data()
counts = df['유형'].value_counts()

# ── 상단 지표 카드 ────────────────────────────────────────────
cols = st.columns(len(TYPE_ORDER))
for col, t in zip(cols, TYPE_ORDER):
    n = int(counts.get(t, 0))
    col.metric(label=f"{TYPE_EMOJI[t]} {t}", value=f"{n}건")

st.divider()

# ── 유형별 집계 바 차트 ──────────────────────────────────────
left, right = st.columns([1, 1])

with left:
    st.subheader('📊 유형별 집계')
    labels = TYPE_ORDER
    values = [int(counts.get(t, 0)) for t in labels]
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.bar(labels, values, color='#3B82F6')
    ax.set_ylabel('건수')
    ax.set_ylim(0, max(values) + 1)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

with right:
    st.subheader('⭐ 별점 분포')
    rating_series = df['별점'].dropna().astype(int).value_counts().sort_index()
    r_labels = [f'{"★" * r}' for r in rating_series.index]
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.bar(r_labels, rating_series.values, color='#F5A623')
    ax.set_ylabel('건수')
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

st.divider()

# ── 급한 불만 Top 3 ───────────────────────────────────────────
st.subheader('🚨 급한 불만 Top 3 (별점 낮은 순)')

complaints = (
    df[df['유형'] == '불만']
    .sort_values('별점', ascending=True, na_position='last')
    .head(3)
    .reset_index(drop=True)
)

if complaints.empty:
    st.info('불만 피드백이 없습니다.')
else:
    for i, row in complaints.iterrows():
        rating_str = f"{'★' * int(row['별점'])}{'☆' * (5 - int(row['별점']))}" if pd.notna(row['별점']) else '별점 없음'
        with st.container(border=True):
            rank_col, content_col = st.columns([1, 10])
            rank_col.markdown(f"### {i + 1}위")
            with content_col:
                st.markdown(f"**[{row['경로']}]** {row['내용']}")
                st.caption(f"{rating_str} &nbsp;|&nbsp; {row['받은날짜']}")

st.divider()

# ── 전체 데이터 테이블 ────────────────────────────────────────
with st.expander('📋 전체 피드백 보기', expanded=False):
    type_filter = st.multiselect(
        '유형 필터',
        options=TYPE_ORDER,
        default=TYPE_ORDER,
    )
    filtered = df[df['유형'].isin(type_filter)][['받은날짜', '경로', '별점', '유형', '내용']]

    def highlight_type(row):
        color = TYPE_COLOR.get(row['유형'], '#ffffff')
        return [f'background-color: {color}22' if col == '유형' else '' for col in row.index]

    st.dataframe(
        filtered.style.apply(highlight_type, axis=1),
        use_container_width=True,
        hide_index=True,
    )
