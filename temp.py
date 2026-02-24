import pandas as pd

# 1. 파일 로드
df_ev = pd.read_csv("최종.csv", encoding="utf-8-sig")
df_normal = pd.read_csv("일반차_tidy.csv", encoding="utf-8-sig")

# 2. '연월'에서 숫자만 추출하여 'year' 컬럼 만들기 (형식 통일)
# '2026년 1월' -> 2026 (정수형)
df_normal['year'] = df_normal['연월'].str.extract('(\d+)').astype(int)

# 3. 데이터 병합 (지역과 연도 기준)
# df_ev의 컬럼: region, year, count_ev
# df_normal의 컬럼: 지역, 연월, 일반차, year
df_merged = pd.merge(
    df_ev, 
    df_normal[['지역', 'year', '일반차']], 
    left_on=['region', 'year'], 
    right_on=['지역', 'year'], 
    how='inner'
)

# 4. 중복된 '지역' 컬럼 제거 및 정리
df_merged = df_merged.drop(columns=['지역'])

# 5. 결과 확인
print(df_merged.head())

# CSV로 저장
df_merged.to_csv("전기차_일반차_통합.csv", index=False, encoding="utf-8-sig")