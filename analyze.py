import pandas as pd


KEYWORDS = {
    '불만': ['오류', '느려', '불편', '안돼', '문제', '달아', '별로', '이상'],
    '요청': ['있으면', '원해요', '해주세요', '추가', '개선'],
    '칭찬': ['좋아요', '친절', '깨끗', '맛있', '최고'],
    '문의': ['언제', '어떻게', '되나요', '알려'],
}
TYPE_ORDER = ['불만', '요청', '칭찬', '문의', '기타']


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


def main() -> None:
    df = read_csv('feedback.csv')

    df['별점'] = pd.to_numeric(df['별점'], errors='coerce')
    df['유형'] = df['내용'].apply(classify)

    # 유형별 집계
    counts = df['유형'].value_counts()
    print("=== 유형별 집계 ===")
    for t in TYPE_ORDER:
        n = counts.get(t, 0)
        if n:
            print(f"{t} : {n}건")

    # 불만 Top 3 (별점 낮은 순, 결측은 맨 뒤)
    complaints = (
        df[df['유형'] == '불만']
        .sort_values('별점', ascending=True, na_position='last')
        .head(3)
    )

    print("\n=== 급한 불만 Top3 ===")
    for i, (_, row) in enumerate(complaints.iterrows(), 1):
        channel = row['경로'] if pd.notna(row.get('경로', float('nan'))) else ''
        content = row['내용'] if pd.notna(row['내용']) else ''
        print(f"{i}. [{channel}] {content}")


if __name__ == '__main__':
    main()
