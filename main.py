import datetime
import requests
import streamlit as st

# Streamlit 페이지 기본 설정
st.set_page_config(page_title="MLB 선수 검색 시스템", page_icon="⚾", layout="wide")


# -------------------------------------------------------------------
# MLB API 함수 모음
# -------------------------------------------------------------------
@st.cache_data(ttl=3600)
def search_player(name):
    """선수 이름 검색"""
    url = f"https://statsapi.mlb.com/api/v1/people/search?names={name}"
    res = requests.get(url).json()
    return res.get("people", [])


@st.cache_data(ttl=3600)
def get_player_info(player_id):
    """선수 상세 프로필 (국적, 포지션, 팀 등)"""
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}"
    res = requests.get(url).json()
    people = res.get("people", [])
    return people[0] if people else {}


@st.cache_data(ttl=3600)
def get_player_stats(player_id):
    """시즌 성적 조회 (타자/투수)"""
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}?hydrate=stats(group=[hitting,pitching],type=[season])"
    res = requests.get(url).json()
    people = res.get("people", [])
    if people and "stats" in people[0]:
        return people[0]["stats"]
    return []


@st.cache_data(ttl=1800)
def get_game_schedule(team_id):
    """팀의 오늘 경기 일정 조회 (MLB 현지 기준)"""
    today = datetime.date.today().strftime("%Y-%m-%d")
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={team_id}&startDate={today}&endDate={today}"
    res = requests.get(url).json()
    dates = res.get("dates", [])
    if dates:
        return dates[0].get("games", [])
    return []


# -------------------------------------------------------------------
# 보완 데이터 (등장곡/응원가, 계약 정보, WAR, 주요 구종 DB)
# MLB Official API에 없거나 수동 매핑이 필요한 데이터
# -------------------------------------------------------------------
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
    """외부 데이터 매핑 (목록에 없는 선수는 기본 메세지 출력)"""
    return PLAYER_DATABASE.get(
        player_name,
        {
            "song": "정보 미등록",
            "contract": "계약 정보 미등록 (별도 확인 필요)",
            "war": "N/A",
            "pitches": "정보 미등록 (Fastball, Changeup 등)",
            "role": "투수/타자",
        },
    )


# -------------------------------------------------------------------
# 메인 UI
# -------------------------------------------------------------------
st.title("⚾ MLB 선수 정보 및 경기 일정 검색기")
st.write(
    "MLB 선수 검색 앱입니다. 탭을 선택하여 **타자** 또는 **투수** 정보를 조회하세요."
)

tab_batter, tab_pitcher = st.tabs(["🏏 타자 검색", "⚾ 투수 검색"])

# -------------------------------------------------------------------
# [1] 타자 검색 탭
# -------------------------------------------------------------------
with tab_batter:
    st.subheader("타자 검색")
    search_b = st.text_input(
        "타자 이름을 영문으로 입력하세요:",
        placeholder="예: Shohei Ohtani, Aaron Judge",
        key="b_search",
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

            st.markdown(f"## 👤 {p_info.get('fullName')}")

            # 기본 프로필 카드 (국적, 포지션)
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                st.info(f"🌐 **국적 / 출생국가:** {p_info.get('birthCountry', '알 수 없음')}")
            with col_b2:
                pos = p_info.get("primaryPosition", {}).get("name", "타자")
                st.info(f"⚾ **포지션:** {pos}")

            # 부가 정보 (등장곡, 계약 조건)
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"🎵 **등장곡 / 응원가:** {db_info['song']}")
            with c2:
                st.write(f"💰 **계약 기간 및 총액:** {db_info['contract']}")

            # 경기 일정
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
                        st.success(
                            f"**[경기 진행 정보]** {away} vs {home} (상태: {status})"
                        )
                else:
                    st.write("오늘 예정된 팀 경기가 없거나 비시즌입니다.")
            else:
                st.write("소속 팀 정보를 확인할 수 없습니다.")

            # 타자 성적
            st.markdown("---")
            st.markdown("#### 📊 타격 기록 및 지표")
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
            else:
                st.warning("올 시즌 타력 기록이 제공되지 않습니다.")

# -------------------------------------------------------------------
# [2] 투수 검색 탭
# -------------------------------------------------------------------
with tab_pitcher:
    st.subheader("투수 검색")
    search_p = st.text_input(
        "투수 이름을 영문으로 입력하세요:",
        placeholder="예: Yoshinobu Yamamoto, Shohei Ohtani",
        key="p_search",
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

            st.markdown(f"## 👤 {p_info.get('fullName')}")

            # 기본 프로필 카드 (국적, 보직)
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.info(f"🌐 **국적 / 출생국가:** {p_info.get('birthCountry', '알 수 없음')}")
            with col_p2:
                role = db_info.get("role", "투수")
                st.info(f"⚾ **보직 (선발/불펜):** {role}")

            # 부가 정보 (등장곡, 계약 조건)
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"🎵 **등장곡:** {db_info['song']}")
            with c2:
                st.write(f"💰 **계약 기간 및 총액:** {db_info['contract']}")

            # 구종 정보
            st.write(f"🎯 **사용 구종:** {db_info['pitches']}")

            # 경기 일정
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
                        st.success(
                            f"**[경기 진행 정보]** {away} vs {home} (상태: {status})"
                        )
                else:
                    st.write("오늘 예정된 팀 경기가 없거나 비시즌입니다.")
            else:
                st.write("소속 팀 정보를 확인할 수 없습니다.")

            # 투수 성적
            st.markdown("---")
            st.markdown("#### 📊 투구 기록 및 지표")
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
                c_era.metric("평균자책점 (ERA)", pitching_stat.get("era", "0.00"))
                c_war.metric("WAR", db_info["war"])
            else:
                st.warning("올 시즌 투구 기록이 제공되지 않습니다.")
