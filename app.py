import streamlit as st
from neo4j import GraphDatabase
from pathlib import Path


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="ระบบแนะนำสัตว์เลี้ยง",
    page_icon="🐾",
    layout="wide"
)

st.markdown("""
<style>
/* ===== ขยายตัวหนังสือและช่องกรอกของหน้าหลัก ===== */
[data-testid="stAppViewContainer"] {
    font-size: 20px;
}

[data-testid="stSidebar"] {
    font-size: 21px;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    font-size: 27px !important;
}

[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
    font-size: 20px;
    line-height: 1.7;
}

[data-testid="stWidgetLabel"] p {
    font-size: 20px !important;
    font-weight: 600 !important;
}

[data-baseweb="select"] {
    min-height: 58px !important;
}

[data-baseweb="select"] > div {
    min-height: 58px !important;
    font-size: 20px !important;
}

[data-baseweb="select"] input {
    font-size: 20px !important;
}

[data-testid="stButton"] button {
    font-size: 20px !important;
    min-height: 52px !important;
    padding: 10px 22px !important;
}

/* ===== หน้าผลการแนะนำสัตว์ ===== */
.pet-section-title {
    color: #D4A017;
    font-weight: bold;
    font-size: 18px;
    margin-top: 10px;
    margin-bottom: 5px;
}

/* ===== หน้าผลการแนะนำสัตว์ ===== */
.pet-result-title {
    font-size: 34px;
    font-weight: 700;
    margin-bottom: 12px;
}

.pet-result-description {
    font-size: 23px;
    line-height: 1.75;
    margin-bottom: 18px;
}

.pet-detail {
    font-size: 19px;
    line-height: 1.7;
    padding: 10px 0;
}

.pet-result-image img {
    border-radius: 14px;
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# IMAGE FOLDER
# =========================================================

IMAGE_DIR = Path(__file__).parent / "images"


def get_pet_image(pet_name):
    extensions = [".jpg", ".jpeg", ".png", ".webp"]

    for extension in extensions:
        image_path = IMAGE_DIR / (pet_name.lower() + extension)

        if image_path.exists():
            return image_path

    return None


# =========================================================
# SIDEBAR MENU
# =========================================================

st.sidebar.title("🐾 ระบบแนะนำสัตว์เลี้ยง")

page = st.sidebar.radio(
    "เมนู",
    [
        "🏠 หน้าหลัก",
        "🐾 คู่มือสัตว์เลี้ยง",
        "🔐 ผู้ดูแลระบบ"
    ]
)


# =========================================================
# NEO4J CONNECTION
# =========================================================

@st.cache_resource
def get_driver():

    driver = GraphDatabase.driver(
        st.secrets["NEO4J_URI"],
        auth=(
            st.secrets["NEO4J_USERNAME"],
            st.secrets["NEO4J_PASSWORD"]
        )
    )

    driver.verify_connectivity()

    return driver


# =========================================================
# HOME PAGE
# =========================================================

if page == "🏠 หน้าหลัก":

    st.title("🐾 ระบบแนะนำสัตว์เลี้ยง")

    st.write(
        "ค้นหาสัตว์เลี้ยงที่เหมาะกับไลฟ์สไตล์ของคุณ"
    )

    st.subheader("ข้อมูลเกี่ยวกับไลฟ์สไตล์ของคุณ")

    user_space_th = st.selectbox(
        "คุณอาศัยอยู่ที่ไหน?",
        [
            "บ้าน",
            "คอนโด",
            "ฟาร์ม",
            "พื้นที่กลางแจ้ง"
        ]
    )

    space_map = {
        "บ้าน": "House",
        "คอนโด": "Condo",
        "ฟาร์ม": "Farm",
        "พื้นที่กลางแจ้ง": "Outdoor Space"
    }

    user_space = space_map[user_space_th]

    user_budget_th = st.selectbox(
        "งบประมาณสำหรับสัตว์เลี้ยงของคุณ?",
        [
            "ต่ำ",
            "ปานกลาง",
            "สูง"
        ]
    )

    budget_map = {
        "ต่ำ": "Low",
        "ปานกลาง": "Medium",
        "สูง": "High"
    }

    user_budget = budget_map[user_budget_th]

    user_time_th = st.selectbox(
        "คุณมีเวลาในการดูแลสัตว์เลี้ยงมากแค่ไหน?",
        [
            "น้อย",
            "ปานกลาง",
            "มาก"
        ]
    )

    time_map = {
        "น้อย": "Low",
        "ปานกลาง": "Medium",
        "มาก": "High"
    }

    user_time = time_map[user_time_th]

    if st.button("🐾 แนะนำสัตว์เลี้ยง"):

        try:

            driver = get_driver()

            result = driver.execute_query(
                """
                MATCH (p:Pet)

                OPTIONAL MATCH
                    (p)-[:SUITABLE_FOR]->(space:LivingSpace)

                OPTIONAL MATCH
                    (p)-[:COST_LEVEL]->(budget:Budget)

                OPTIONAL MATCH
                    (p)-[:NEEDS_TIME]->(time:TimeAvailable)

                WITH
                    p,
                    collect(DISTINCT space.name) AS spaces,
                    collect(DISTINCT budget.name)[0] AS budget,
                    collect(DISTINCT time.name)[0] AS time

                WITH
                    p,
                    spaces,
                    budget,
                    time,

                    CASE
                        WHEN $space IN spaces THEN 1
                        ELSE 0
                    END +

                    CASE
                        WHEN budget = $budget THEN 1
                        ELSE 0
                    END +

                    CASE
                        WHEN time = $time THEN 1
                        ELSE 0
                    END AS score

                RETURN
                    p.name AS Pet,
                    p.description AS Description,
                    score AS Score,
                    spaces AS SuitableSpace,
                    budget AS Budget,
                    time AS TimeAvailable

                ORDER BY Score DESC, Pet
                """,
                space=user_space,
                budget=user_budget,
                time=user_time
            )

            st.subheader("🐾 สัตว์เลี้ยงที่แนะนำ")

            space_display_map = {
                "House": "บ้าน",
                "Condo": "คอนโด",
                "Farm": "ฟาร์ม",
                "Outdoor Space": "พื้นที่กลางแจ้ง"
            }

            budget_display_map = {
                "Low": "ต่ำ",
                "Medium": "ปานกลาง",
                "High": "สูง"
            }

            time_display_map = {
                "Low": "น้อย",
                "Medium": "ปานกลาง",
                "High": "มาก"
            }

            # แปลงข้อมูลที่แสดงผลจาก Neo4j ให้เป็นภาษาไทย
            pet_display_map = {
                "Dog": "สุนัข",
                "Cat": "แมว",
                "Bird": "นก",
                "Rabbit": "กระต่าย",
                "Fish": "ปลา",
                "Hamster": "แฮมสเตอร์",
                "Duck": "เป็ด",
                "Sheep": "แกะ",
                "Turtle": "เต่า",
                "Horse": "ม้า"
            }

            # คำอธิบายภาษาไทยสำหรับสัตว์แต่ละชนิด
            description_display_map = {
                "Dog":
                    "สุนัขเป็นสัตว์เลี้ยงที่เป็นมิตรและชอบอยู่ร่วมกับผู้คน เหมาะสำหรับผู้ที่มีเวลาในการดูแลและพาออกกำลังกาย",
                "Cat":
                    "แมวเป็นสัตว์เลี้ยงที่รักอิสระและสามารถปรับตัวให้เข้ากับสภาพแวดล้อมภายในบ้านได้ดี",
                "Bird":
                    "นกเป็นสัตว์เลี้ยงขนาดเล็กที่มีความกระตือรือร้นและสามารถสร้างความเพลิดเพลินให้กับผู้เลี้ยงได้",
                "Rabbit":
                    "กระต่ายเป็นสัตว์เลี้ยงขนาดเล็กที่มีนิสัยอ่อนโยนและค่อนข้างเงียบ เหมาะสำหรับผู้ที่ชอบสัตว์เลี้ยงที่สงบ",
                "Fish":
                    "ปลาเป็นสัตว์เลี้ยงที่เงียบและเหมาะสำหรับผู้ที่ต้องการสัตว์เลี้ยงที่ใช้พื้นที่ไม่มาก",
                "Hamster":
                    "แฮมสเตอร์เป็นสัตว์เลี้ยงขนาดเล็กที่สามารถเลี้ยงในพื้นที่จำกัด และมีพฤติกรรมที่น่าสนใจให้สังเกต",
                "Duck":
                    "เป็ดเป็นสัตว์ที่ชอบอยู่รวมกันและต้องการพื้นที่สำหรับเดินเล่นและทำกิจกรรมกลางแจ้ง",
                "Sheep":
                    "แกะเป็นสัตว์เลี้ยงในพื้นที่เกษตรที่มักอยู่รวมกันเป็นฝูง และต้องการพื้นที่สำหรับใช้ชีวิตอย่างเหมาะสม",
                "Turtle":
                    "เต่าเป็นสัตว์ที่ค่อนข้างสงบและเงียบ เหมาะสำหรับผู้ที่ชอบสังเกตพฤติกรรมของสัตว์",
                "Horse":
                    "ม้าเป็นสัตว์ขนาดใหญ่ที่มีความกระตือรือร้น และต้องการพื้นที่กว้างสำหรับการเคลื่อนไหวและออกกำลังกาย"
            }

            for record in result.records:

                st.markdown("---")

                pet_name = pet_display_map.get(
                    record["Pet"],
                    record["Pet"]
                )

                # ใช้คำอธิบายภาษาไทยที่กำหนดไว้เสมอ
                # เพื่อไม่ให้ข้อความภาษาอังกฤษจาก Neo4j แสดงบนหน้าจอ
                description = description_display_map.get(
                    record["Pet"],
                    "ยังไม่มีคำอธิบายภาษาไทยสำหรับสัตว์ชนิดนี้"
                )

                # แสดงรูปทางซ้าย และขยายรายละเอียดทางขวาให้อ่านง่ายขึ้น
                image_col, info_col = st.columns([1.25, 3.75], gap="large")

                with image_col:
                    image_path = get_pet_image(record["Pet"])

                    if image_path:
                        st.markdown('<div class="pet-result-image">', unsafe_allow_html=True)
                        st.image(
                            str(image_path),
                            width=240
                        )
                        st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.info(f"ไม่พบรูปของ {pet_name}")

                with info_col:
                    st.markdown(
                        f'<div class="pet-result-title">🐾 {pet_name} — {record["Score"]}/3</div>',
                        unsafe_allow_html=True
                    )

                    st.markdown(
                        f'<div class="pet-result-description">{description}</div>',
                        unsafe_allow_html=True
                    )

                    col1, col2, col3 = st.columns(3, gap="medium")

                    with col1:
                        suitable_spaces = [
                            space_display_map.get(space, space)
                            for space in record["SuitableSpace"]
                        ]

                        st.markdown(
                            '<div class="pet-detail">🏠 <b>พื้นที่ที่เหมาะสม</b><br>'
                            + ", ".join(suitable_spaces)
                            + '</div>',
                            unsafe_allow_html=True
                        )

                    with col2:
                        st.markdown(
                            '<div class="pet-detail">💰 <b>งบประมาณ</b><br>'
                            + budget_display_map.get(record['Budget'], record['Budget'])
                            + '</div>',
                            unsafe_allow_html=True
                        )

                    with col3:
                        st.markdown(
                            '<div class="pet-detail">⏰ <b>เวลาที่ใช้ดูแล</b><br>'
                            + time_display_map.get(record['TimeAvailable'], record['TimeAvailable'])
                            + '</div>',
                            unsafe_allow_html=True
                        )

        except Exception as e:

            st.error(
                "ไม่สามารถเชื่อมต่อกับ Neo4j ได้"
            )

            st.write(str(e))


# =========================================================
# PET GUIDE PAGE
# =========================================================

elif page == "🐾 คู่มือสัตว์เลี้ยง":

    st.title("🐾 คู่มือแนะนำสัตว์เลี้ยง")

    st.write(
        "ทำความรู้จักกับสัตว์เลี้ยงแต่ละประเภท "
        "ลักษณะนิสัย ลักษณะทั่วไป และการดูแลเบื้องต้น"
    )

    st.markdown("---")

    pets = [

        {
            "name": "Dog",
            "title": "สุนัข",
            "personality": "เป็นมิตร เข้าสังคม และชอบทำกิจกรรม",
            "description":
                "สุนัขเป็นสัตว์เลี้ยงที่เป็นมิตรและชอบอยู่ร่วมกับผู้คน "
                "เหมาะสำหรับผู้ที่มีเวลาในการดูแลและพาออกกำลังกาย",
            "care":
                "ต้องการอาหาร น้ำสะอาด การออกกำลังกาย "
                "การดูแลสุขภาพ และการเอาใจใส่อย่างสม่ำเสมอ"
        },

        {
            "name": "Cat",
            "title": "แมว",
            "personality": "รักอิสระ ปรับตัวได้ดี และค่อนข้างสงบ",
            "description":
                "แมวเป็นสัตว์เลี้ยงที่รักอิสระและสามารถปรับตัว "
                "ให้เข้ากับสภาพแวดล้อมภายในบ้านได้ดี",
            "care":
                "ต้องการอาหาร น้ำสะอาด กระบะทราย "
                "พื้นที่สำหรับพักผ่อน และการดูแลสุขภาพอย่างสม่ำเสมอ"
        },

        {
            "name": "Bird",
            "title": "นก",
            "personality": "ชอบเข้าสังคม กระตือรือร้น และร่าเริง",
            "description":
                "นกเป็นสัตว์เลี้ยงขนาดเล็กที่มีความกระตือรือร้น "
                "และสามารถสร้างความเพลิดเพลินให้กับผู้เลี้ยงได้",
            "care":
                "ต้องการกรงที่เหมาะสม อาหาร น้ำสะอาด "
                "และการดูแลความสะอาดของกรงอย่างสม่ำเสมอ"
        },

        {
            "name": "Rabbit",
            "title": "กระต่าย",
            "personality": "อ่อนโยน สงบ และไม่ก้าวร้าว",
            "description":
                "กระต่ายเป็นสัตว์เลี้ยงขนาดเล็กที่มีนิสัยอ่อนโยน "
                "และค่อนข้างเงียบ เหมาะสำหรับผู้ที่ชอบสัตว์เลี้ยงที่สงบ",
            "care":
                "ต้องการพื้นที่อยู่อาศัยที่สะอาด อาหารที่เหมาะสม "
                "น้ำสะอาด และการดูแลสุขภาพอย่างสม่ำเสมอ"
        },

        {
            "name": "Fish",
            "title": "ปลา",
            "personality": "สงบ เงียบ และดูแลง่าย",
            "description":
                "ปลาเป็นสัตว์เลี้ยงที่เงียบและเหมาะสำหรับผู้ที่ต้องการ "
                "สัตว์เลี้ยงที่ใช้พื้นที่ไม่มาก",
            "care":
                "ต้องการตู้ปลาที่เหมาะสม น้ำสะอาด "
                "อาหารที่เหมาะสม และการดูแลคุณภาพน้ำเป็นประจำ"
        },

        {
            "name": "Hamster",
            "title": "แฮมสเตอร์",
            "personality": "ตัวเล็ก กระตือรือร้น และชอบสำรวจ",
            "description":
                "แฮมสเตอร์เป็นสัตว์เลี้ยงขนาดเล็กที่สามารถเลี้ยง "
                "ในพื้นที่จำกัด และมีพฤติกรรมที่น่าสนใจให้สังเกต",
            "care":
                "ต้องการกรงที่สะอาด อาหาร น้ำสะอาด "
                "และอุปกรณ์สำหรับออกกำลังกายที่เหมาะสม"
        },

        {
            "name": "Duck",
            "title": "เป็ด",
            "personality": "ชอบเข้าสังคม กระตือรือร้น และชอบอยู่รวมกัน",
            "description":
                "เป็ดเป็นสัตว์ที่ชอบอยู่รวมกันและต้องการพื้นที่ "
                "สำหรับเดินเล่นและทำกิจกรรมกลางแจ้ง",
            "care":
                "ต้องการพื้นที่กลางแจ้ง น้ำสะอาด อาหารที่เหมาะสม "
                "ที่พักอาศัย และการดูแลอย่างสม่ำเสมอ"
        },

        {
            "name": "Sheep",
            "title": "แกะ",
            "personality": "รักสงบ ชอบอยู่รวมกัน และเข้าสังคมได้ดี",
            "description":
                "แกะเป็นสัตว์เลี้ยงในพื้นที่เกษตรที่มักอยู่รวมกันเป็นฝูง "
                "และต้องการพื้นที่สำหรับใช้ชีวิตอย่างเหมาะสม",
            "care":
                "ต้องการพื้นที่สำหรับเลี้ยง อาหาร น้ำสะอาด "
                "ที่พัก และการดูแลสุขภาพอย่างเหมาะสม"
        },

        {
            "name": "Turtle",
            "title": "เต่า",
            "personality": "สงบ เงียบ และเคลื่อนไหวช้า",
            "description":
                "เต่าเป็นสัตว์ที่ค่อนข้างสงบและเงียบ "
                "เหมาะสำหรับผู้ที่ชอบสังเกตพฤติกรรมของสัตว์",
            "care":
                "ต้องการพื้นที่อยู่อาศัยที่เหมาะสม "
                "อาหารที่เหมาะกับชนิดของเต่า น้ำสะอาด "
                "และการดูแลสภาพแวดล้อมอย่างสม่ำเสมอ"
        },

        {
            "name": "Horse",
            "title": "ม้า",
            "personality": "กระตือรือร้น แข็งแรง และต้องการการเคลื่อนไหว",
            "description":
                "ม้าเป็นสัตว์ขนาดใหญ่ที่มีความกระตือรือร้น "
                "และต้องการพื้นที่กว้างสำหรับการเคลื่อนไหวและออกกำลังกาย",
            "care":
                "ต้องการพื้นที่กลางแจ้งขนาดใหญ่ อาหาร น้ำสะอาด "
                "การออกกำลังกาย และการดูแลสุขภาพอย่างสม่ำเสมอ"
        }

    ]

    for i in range(0, len(pets), 3):

        columns = st.columns(3)

        for j, col in enumerate(columns):

            if i + j >= len(pets):
                continue

            pet = pets[i + j]

            with col:

                # กรอบแยกข้อมูลสัตว์แต่ละตัว
                with st.container(border=True):

                    image_path = get_pet_image(
                        pet["name"]
                    )

                    if image_path:

                        st.image(
                            str(image_path),
                            use_container_width=True
                        )

                    else:

                        st.warning(
                            f"ไม่พบรูปของ {pet['title']}"
                        )

                    st.subheader(
                        f"🐾 {pet['title']}"
                    )

                    st.markdown(
                        '<div class="pet-section-title">ลักษณะนิสัย</div>',
                        unsafe_allow_html=True
                    )
                    st.write(pet["personality"])

                    st.markdown(
                        '<div class="pet-section-title">ลักษณะทั่วไป</div>',
                        unsafe_allow_html=True
                    )
                    st.write(pet["description"])

                    st.markdown(
                        '<div class="pet-section-title">การดูแลเบื้องต้น</div>',
                        unsafe_allow_html=True
                    )
                    st.write(pet["care"])

    st.info(
        "💡 ข้อมูลในหน้านี้ใช้สำหรับแนะนำลักษณะทั่วไปของสัตว์ "
        "ส่วนการเลือกสัตว์ที่เหมาะสมกับผู้ใช้งาน "
        "สามารถใช้ระบบแนะนำจากหน้า Home ได้"
    )


# =========================================================
# ADMIN PAGE
# =========================================================

elif page == "🔐 ผู้ดูแลระบบ":

    st.title("🔐 ผู้ดูแลระบบ")

    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    # =====================================================
    # LOGIN
    # =====================================================

    if not st.session_state.admin_logged_in:

        st.subheader("🔑 เข้าสู่ระบบผู้ดูแล")

        with st.form("admin_login_form"):

            username = st.text_input("ชื่อผู้ใช้")
            password = st.text_input("รหัสผ่าน", type="password")

            login_submit = st.form_submit_button(
                "🔐 เข้าสู่ระบบ",
                use_container_width=True
            )

        if login_submit:

            # สำหรับงานส่ง/เดโม
            # Username: admin
            # Password: admin123
            if username == "admin" and password == "admin123":

                st.session_state.admin_logged_in = True
                st.success("เข้าสู่ระบบผู้ดูแลสำเร็จ")
                st.rerun()

            else:
                st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    # =====================================================
    # DASHBOARD
    # =====================================================

    else:

        st.title("🔧 แผงควบคุมผู้ดูแลระบบ")

        top_col1, top_col2 = st.columns([4, 1])

        with top_col1:
            st.success("เข้าสู่ระบบผู้ดูแลเรียบร้อยแล้ว")

        with top_col2:
            if st.button("🚪 ออกจากระบบ", use_container_width=True):
                st.session_state.admin_logged_in = False
                st.rerun()

        st.markdown("---")

        # =================================================
        # DATABASE CONNECTION / STATS
        # =================================================

        try:
            driver = get_driver()

            count_result = driver.execute_query(
                "MATCH (p:Pet) RETURN count(p) AS total"
            )
            total_pets = count_result.records[0]["total"]

            stat_col1, stat_col2, stat_col3 = st.columns(3)

            with stat_col1:
                st.metric("🐾 จำนวนสัตว์เลี้ยง", total_pets)

            with stat_col2:
                space_count = driver.execute_query(
                    "MATCH (n:LivingSpace) RETURN count(n) AS total"
                ).records[0]["total"]
                st.metric("🏠 พื้นที่", space_count)

            with stat_col3:
                budget_count = driver.execute_query(
                    "MATCH (n:Budget) RETURN count(n) AS total"
                ).records[0]["total"]
                st.metric("💰 ระดับงบประมาณ", budget_count)

        except Exception as e:
            st.error("ไม่สามารถเชื่อมต่อกับ Neo4j ได้")
            st.write(str(e))
            st.stop()

        st.markdown("---")

        # =================================================
        # ADD PET
        # =================================================

        st.subheader("➕ เพิ่มสัตว์เลี้ยง")

        with st.form("add_pet_form", clear_on_submit=True):

            add_col1, add_col2 = st.columns(2)

            with add_col1:
                new_pet_name = st.text_input("ชื่อสัตว์เลี้ยง")

            with add_col2:
                new_pet_description = st.text_area("รายละเอียด")

            add_col3, add_col4, add_col5 = st.columns(3)

            with add_col3:
                new_pet_space_th = st.selectbox(
                    "พื้นที่ที่เหมาะสม",
                    ["บ้าน", "คอนโด", "ฟาร์ม", "พื้นที่กลางแจ้ง"]
                )

            with add_col4:
                new_pet_budget_th = st.selectbox(
                    "งบประมาณ",
                    ["ต่ำ", "ปานกลาง", "สูง"]
                )

            with add_col5:
                new_pet_time_th = st.selectbox(
                    "เวลาที่ใช้ดูแล",
                    ["น้อย", "ปานกลาง", "มาก"]
                )

            add_submit = st.form_submit_button(
                "➕ เพิ่มสัตว์เลี้ยง",
                use_container_width=True
            )

        space_to_db = {
            "บ้าน": "House",
            "คอนโด": "Condo",
            "ฟาร์ม": "Farm",
            "พื้นที่กลางแจ้ง": "Outdoor Space"
        }

        budget_to_db = {
            "ต่ำ": "Low",
            "ปานกลาง": "Medium",
            "สูง": "High"
        }

        time_to_db = {
            "น้อย": "Low",
            "ปานกลาง": "Medium",
            "มาก": "High"
        }

        if add_submit:

            name = new_pet_name.strip()
            description = new_pet_description.strip()

            if not name or not description:
                st.warning("กรุณากรอกชื่อและรายละเอียดสัตว์เลี้ยง")

            else:
                try:
                    existing = driver.execute_query(
                        "MATCH (p:Pet {name: $name}) RETURN p LIMIT 1",
                        name=name
                    )

                    if existing.records:
                        st.warning(f"มีสัตว์เลี้ยงชื่อ {name} อยู่แล้ว ไม่สามารถเพิ่มชื่อซ้ำได้")

                    else:
                        driver.execute_query(
                            """
                            CREATE (p:Pet {
                                name: $name,
                                description: $description
                            })

                            WITH p

                            MERGE (space:LivingSpace {name: $space})
                            MERGE (budget:Budget {name: $budget})
                            MERGE (time:TimeAvailable {name: $time})

                            CREATE (p)-[:SUITABLE_FOR]->(space)
                            CREATE (p)-[:COST_LEVEL]->(budget)
                            CREATE (p)-[:NEEDS_TIME]->(time)
                            """,
                            name=name,
                            description=description,
                            space=space_to_db[new_pet_space_th],
                            budget=budget_to_db[new_pet_budget_th],
                            time=time_to_db[new_pet_time_th]
                        )

                        st.success(f"เพิ่ม {name} สำเร็จ")
                        st.rerun()

                except Exception as e:
                    st.error("ไม่สามารถเพิ่มข้อมูลได้")
                    st.write(str(e))

        st.markdown("---")

        # =================================================
        # MANAGE PETS
        # =================================================

        st.subheader("🐾 จัดการข้อมูลสัตว์เลี้ยง")

        try:

            result = driver.execute_query(
                """
                MATCH (p:Pet)

                OPTIONAL MATCH (p)-[:SUITABLE_FOR]->(space:LivingSpace)
                OPTIONAL MATCH (p)-[:COST_LEVEL]->(budget:Budget)
                OPTIONAL MATCH (p)-[:NEEDS_TIME]->(time:TimeAvailable)

                RETURN
                    p.name AS name,
                    p.description AS description,
                    collect(DISTINCT space.name)[0] AS space,
                    collect(DISTINCT budget.name)[0] AS budget,
                    collect(DISTINCT time.name)[0] AS time

                ORDER BY name
                """
            )

            if not result.records:
                st.info("ยังไม่มีข้อมูลสัตว์เลี้ยงใน Neo4j")

            db_to_space = {v: k for k, v in space_to_db.items()}
            db_to_budget = {v: k for k, v in budget_to_db.items()}
            db_to_time = {v: k for k, v in time_to_db.items()}

            spaces = list(space_to_db.keys())
            budgets = list(budget_to_db.keys())
            times = list(time_to_db.keys())

            for index, record in enumerate(result.records):

                pet_name = record["name"]

                with st.expander(f"🐾 {pet_name}", expanded=False):

                    with st.form(f"edit_pet_form_{index}"):

                        edit_name = st.text_input(
                            "ชื่อสัตว์เลี้ยง",
                            value=record["name"] or ""
                        )

                        edit_description = st.text_area(
                            "รายละเอียด",
                            value=record["description"] or ""
                        )

                        current_space = db_to_space.get(record["space"], spaces[0])
                        current_budget = db_to_budget.get(record["budget"], budgets[0])
                        current_time = db_to_time.get(record["time"], times[0])

                        edit_col1, edit_col2, edit_col3 = st.columns(3)

                        with edit_col1:
                            edit_space = st.selectbox(
                                "พื้นที่",
                                spaces,
                                index=spaces.index(current_space)
                            )

                        with edit_col2:
                            edit_budget = st.selectbox(
                                "งบประมาณ",
                                budgets,
                                index=budgets.index(current_budget)
                            )

                        with edit_col3:
                            edit_time = st.selectbox(
                                "เวลาที่ดูแล",
                                times,
                                index=times.index(current_time)
                            )

                        save_submit = st.form_submit_button(
                            "💾 บันทึกการแก้ไข",
                            use_container_width=True
                        )

                    if save_submit:

                        new_name = edit_name.strip()
                        new_description = edit_description.strip()

                        if not new_name or not new_description:
                            st.warning("กรุณากรอกชื่อและรายละเอียดให้ครบ")

                        else:
                            try:
                                # ถ้าเปลี่ยนชื่อ ให้ตรวจสอบชื่อซ้ำก่อน
                                duplicate = driver.execute_query(
                                    """
                                    MATCH (p:Pet {name: $name})
                                    WHERE $old_name <> $name
                                    RETURN p LIMIT 1
                                    """,
                                    old_name=record["name"],
                                    name=new_name
                                )

                                if duplicate.records:
                                    st.warning(f"มีสัตว์เลี้ยงชื่อ {new_name} อยู่แล้ว")

                                else:
                                    driver.execute_query(
                                        """
                                        MATCH (p:Pet {name: $old_name})

                                        SET
                                            p.name = $name,
                                            p.description = $description

                                        WITH p

                                        OPTIONAL MATCH
                                            (p)-[r:SUITABLE_FOR|COST_LEVEL|NEEDS_TIME]->()
                                        DELETE r

                                        WITH p

                                        MERGE (space:LivingSpace {name: $space})
                                        MERGE (budget:Budget {name: $budget})
                                        MERGE (time:TimeAvailable {name: $time})

                                        CREATE (p)-[:SUITABLE_FOR]->(space)
                                        CREATE (p)-[:COST_LEVEL]->(budget)
                                        CREATE (p)-[:NEEDS_TIME]->(time)
                                        """,
                                        old_name=record["name"],
                                        name=new_name,
                                        description=new_description,
                                        space=space_to_db[edit_space],
                                        budget=budget_to_db[edit_budget],
                                        time=time_to_db[edit_time]
                                    )

                                    st.success(f"แก้ไข {new_name} สำเร็จ")
                                    st.rerun()

                            except Exception as e:
                                st.error("ไม่สามารถแก้ไขข้อมูลได้")
                                st.write(str(e))

                    st.markdown("---")
                    st.markdown("**⚠️ การลบข้อมูล**")

                    delete_confirm = st.checkbox(
                        "ฉันยืนยันว่าต้องการลบสัตว์เลี้ยงตัวนี้",
                        key=f"confirm_delete_{index}"
                    )

                    if st.button(
                        "🗑️ ลบสัตว์เลี้ยง",
                        key=f"delete_pet_{index}",
                        disabled=not delete_confirm,
                        use_container_width=True
                    ):

                        try:
                            driver.execute_query(
                                """
                                MATCH (p:Pet {name: $name})
                                DETACH DELETE p
                                """,
                                name=record["name"]
                            )

                            st.success(f"ลบ {record['name']} สำเร็จ")
                            st.rerun()

                        except Exception as e:
                            st.error("ไม่สามารถลบข้อมูลได้")
                            st.write(str(e))

        except Exception as e:
            st.error("ไม่สามารถโหลดข้อมูลสัตว์เลี้ยงได้")
            st.write(str(e))
