import datetime
import requests
import streamlit as st

st.set_page_config(page_title="MLB 선수 검색 System", page_icon="⚾", layout="wide")

# -------------------------------------------------------------------
# 한글-영문 선수 이름 매핑 사전
# -------------------------------------------------------------------
KOREAN_TO_ENGLISH_NAMES = {
    # 주요 한글 성/이름 조합
    "오타니": "Shohei Ohtani",
    "오타니 쇼헤이": "Shohei Ohtani",
    "쇼헤이 오타니": "Shohei Ohtani",
    "저지": "Aaron Judge",
    "애런 저지": "Aaron Judge",
    "에런 저지": "Aaron Judge",
    "야마모토": "Yoshinobu Yamamoto",
    "야마모토 요시노부": "Yoshinobu Yamamoto",
    "김하성": "Ha-Seong Kim",
    "이정후": "Jung Hoo Lee",
    "김혜성": "Hye-Seong Kim",
    "고우석": "Woo-Suk Go",
    "류현진": "Hyun Jin Ryu",
    "최지만": "Ji Man Choi",
    "배지환": "Ji Hwan Bae",
    "트라우트": "Mike Trout",
    "마이크 트라우트": "Mike Trout",
    "베츠": "Mookie Betts",
    "무키 베츠": "Mookie Betts",
    "프리먼": "Freddie Freeman",
    "프레디 프리먼": "Freddie Freeman",
    "커쇼": "Clayton Kershaw",
    "클레이튼 커쇼": "Clayton Kershaw",
    "슈어저": "Max Scherzer",
    "맥스 슈어저": "Max Scherzer",
    "데그롬": "Jacob deGrom",
    "제이콥 데그롬": "Jacob deGrom",
    "소토": "Juan Soto",
    "후안 소토": "Juan Soto",
    "아쿠냐": "Ronald Acuna Jr.",
    "아쿠냐 주니어": "Ronald Acuna Jr.",
}


def translate_korean_to_english(input_name):
    """한글 이름을 영문으로 변환 (사전에 없으면 원래 입력값 반환)"""
    clean_name = input_name.strip()
    return KOREAN_TO_ENGLISH_NAMES.get(clean_name, clean_name)


# -------------------------------------------------------------------
# MLB API 함수 모음
# -------------------------------------------------------------------
@st.cache_data(ttl=3600)
def search_player(name):
    if not name:
        return []
    # 한글 입력 처리
    search_query = translate_korean_to_english(name)
    url = f"https://statsapi.mlb.com/api/v1/people/search?names={search_query}"
    try:
        res = requests.get(url, timeout=5).json()
        return res.get("people", [])
    except Exception:
        return []


@st.cache_data(ttl=3600)
def get_player_info(player_id):
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}"
    try:
        res = requests.get(url, timeout=5).json()
        people = res.get("people", [])
        return people[0] if people else {}
    except Exception:
        return {}


@st.cache_data(ttl=3600)
def get_player_stats(player_id):
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}?hydrate=stats(group=[hitting,pitching],type=[season])"
    try:
        res = requests.get(url, timeout=5).json()
        people = res.get("people", [])
        return people[0].get("stats", []) if people else []
    except Exception:
        return []


@st.cache_data(ttl=1800)
def get_game_schedule(team_id):
    today = datetime.date.today().strftime("%Y-%m-%d")
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={team_id}&startDate={today}&endDate={today}"
    try:
        res = requests.get(url, timeout=5).json()
        dates = res.get("dates", [])
        return dates[0].get("games", []) if dates else []
    except Exception:
        return []


PLAYER_DATABASE = {
    "Shohei Ohtani": {
        "song": "The Greatest Show - Greatest Showman Cast",
        "contract": "10년 $700,000,000 (약 7억 달러)",
        "war": "9.0",
        "pitches": "4-Seam Fastball, Splitter, Sweeper, Cut Fastball",
        "role": "선발투수 / 지명타자",
    },
    "Aaron Judge": {
        "song": "Swag Surfin - Fast Life Yungstaz",
        "contract": "9년 $360,000,000 (약 3.6억 달러)",
        "war": "10.8",
        "pitches": "해당 없음 (타자)",
        "role": "외야수",
    },
    "Yoshinobu Yamamoto": {
        "song": "Frontier - VINAI",
        "contract": "12년 $325,000,000 (약 3.25억 달러)",
        "war": "3.8",
        "pitches": "4-Seam Fastball, Splitter, Curveball, Cutter",
        "role": "선발투수",
    },
}


def get_mock_info(player_name):
    return PLAYER_DATABASE.get(
        player_name,
        {
            "song": "정보 미등록",
            "contract": "계약 정보 미등록 (별도 확인 필요)",
            "war": "N/A",
            "pitches": "정보 미등록",
            "role": "투수/타자",
        },
    )


# -------------------------------------------------------------------
# 메인 UI
# -------------------------------------------------------------------
st.title("⚾ MLB 선수 정보 검색기")

tab_batter, tab_pitcher = st.tabs(["🏏 타자 검색", "⚾ 투수 검색"])

# -------------------------------------------------------------------
# [1] 타자 탭
# -------------------------------------------------------------------
with tab_batter:
    st.subheader("타자 검색")
    search_b = st.text_input(
        "타자 이름을 입력하세요 (한글/영문 지원):",
        placeholder="예: 오타니, 애런 저지, Shohei Ohtani",
        key="batter_input_key",
    )

    if search_b:
        results = search_player(search_b)
        if not results:
            st.error("해당 이름의 선수를 찾지 못했습니다.")
        else:
            player = results[0]
            p_id = player["id"]
            p_info = get_player_info(p_id)
            db_info = get_mock_info(p_info.get("fullName"))

            img_url = f"https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:silo:current.png/w_420,q_auto:best/v1/people/{p_id}/headshot/silo/current.png"

            col_img, col_detail = st.columns([1, 3])

            with col_img:
                st.image(
                    img_url,
                    caption=p_info.get("fullName"),
                    use_container_width=True,
                )

            with col_detail:
                st.markdown(f"### 👤 {p_info.get('fullName')}")
                st.info(f"🌐 **국적:** {p_info.get('birthCountry', '알 수 없음')}")
                pos = p_info.get("primaryPosition", {}).get("name", "타자")
                st.info(f"⚾ **포지션:** {pos}")
                st.write(f"🎵 **등장곡 / 응원가:** {db_info['song']}")
                st.write(f"💰 **계약 정보:** {db_info['contract']}")

            st.markdown("---")
            st.markdown("#### 📅 오늘 경기 일정 (MLB 현지 기준)")
            team_id = p_info.get("currentTeam", {}).get("id")
            if team_id:
                games = get_game_schedule(team_id)
                if games:
                    for g in games:
                        away = g["teams"]["away"]["team"]["name"]
                        home = g["teams"]["home"]["team"]["name"]
                        status = g["status"]["detailedState"]
                        st.success(f"{away} vs {home} | 상태: {status}")
                else:
                    st.write("오늘 예정된 경기가 없습니다.")
            else:
                st.write("소속 팀 정보 없음")

            st.markdown("---")
            st.markdown("#### 📊 타격 기록")
            stats = get_player_stats(p_id)
            hitting_stat = None
            for s in stats:
                if s.get("group", {}).get("displayName") == "hitting":
                    hitting_stat = s["splits"][0]["stat"]
                    break

            if hitting_stat:
                m1, m2, m3, m4, m5, m6 = st.columns(6)
                m1.metric("안타", hitting_stat.get("hits", 0))
                m2.metric("2루타", hitting_stat.get("doubles", 0))
                m3.metric("3루타", hitting_stat.get("triples", 0))
                m4.metric("홈런", hitting_stat.get("homeRuns", 0))
                m5.metric("도루", hitting_stat.get("stolenBases", 0))
                m6.metric("삼진", hitting_stat.get("strikeOuts", 0))

                c_ops, c_war = st.columns(2)
                c_ops.metric("OPS", hitting_stat.get("ops", ".000"))
                c_war.metric("WAR", db_info["war"])

# -------------------------------------------------------------------
# [2] 투수 탭
# -------------------------------------------------------------------
with tab_pitcher:
    st.subheader("투수 검색")
    search_p = st.text_input(
        "투수 이름을 입력하세요 (한글/영문 지원):",
        placeholder="예: 야마모토, 오타니, Yoshinobu Yamamoto",
        key="pitcher_input_key",
    )

    if search_p:
        results = search_player(search_p)
        if not results:
            st.error("해당 이름의 선수를 찾지 못했습니다.")
        else:
            player = results[0]
            p_id = player["id"]
            p_info = get_player_info(p_id)
            db_info = get_mock_info(p_info.get("fullName"))

            img_url = f"https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:silo:current.png/w_420,q_auto:best/v1/people/{p_id}/headshot/silo/current.png"

            col_img, col_detail = st.columns([1, 3])

            with col_img:
                st.image(
                    img_url,
                    caption=p_info.get("fullName"),
                    use_container_width=True,
                )

            with col_detail:
                st.markdown(f"### 👤 {p_info.get('fullName')}")
                st.info(f"🌐 **국적:** {p_info.get('birthCountry', '알 수 없음')}")
                role = db_info.get("role", "투수")
                st.info(f"⚾ **보직:** {role}")
                st.write(f"🎵 **등장곡:** {db_info['song']}")
                st.write(f"💰 **계약 정보:** {db_info['contract']}")
                st.write(f"🎯 **주요 구종:** {db_info['pitches']}")

            st.markdown("---")
            st.markdown("#### 📅 오늘 경기 일정 (MLB 현지 기준)")
            team_id = p_info.get("currentTeam", {}).get("id")
            if team_id:
                games = get_game_schedule(team_id)
                if games:
                    for g in games:
                        away = g["teams"]["away"]["team"]["name"]
                        home = g["teams"]["home"]["team"]["name"]
                        status = g["status"]["detailedState"]
                        st.success(f"{away} vs {home} | 상태: {status}")
                else:
                    st.write("오늘 예정된 경기가 없습니다.")
            else:
                st.write("소속 팀 정보 없음")

            st.markdown("---")
            st.markdown("#### 📊 투구 기록")
            stats = get_player_stats(p_id)
            pitching_stat = None
            for s in stats:
                if s.get("group", {}).get("displayName") == "pitching":
                    pitching_stat = s["splits"][0]["stat"]
                    break

            if pitching_stat:
                p1, p2, p3, p4 = st.columns(4)
                p1.metric("탈삼진", pitching_stat.get("strikeOuts", 0))
                p2.metric("볼넷", pitching_stat.get("baseOnBalls", 0))
                p3.metric("피안타", pitching_stat.get("hits", 0))
                p4.metric("피홈런", pitching_stat.get("homeRuns", 0))

                c_era, c_war = st.columns(2)
                c_era.metric("ERA", pitching_stat.get("era", "0.00"))
                c_war.metric("WAR", db_info["war"])
