# app.py

from __future__ import annotations

import pandas as pd
import streamlit as st

from neo4j_service import (
    get_all_pets,
    get_dashboard_metrics,
    get_pet_relationships,
    ping,
    recommend_pets,
    search_pets,
    seed_demo_data,
)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Pet Recommendation System",
    page_icon="🐾",
    layout="wide",
)


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    .hero {
        padding: 2rem;
        border-radius: 20px;
        background: linear-gradient(
            135deg,
            #164e63,
            #0f766e
        );
        color: white;
        margin-bottom: 25px;
    }

    .hero h1 {
        font-size: 2.4rem;
        margin-bottom: 10px;
    }

    .hero p {
        font-size: 1.05rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# CONNECTION CHECK
# =========================================================

def check_connection():

    try:

        if ping():
            return True

        return False

    except Exception as e:

        st.error(
            "ไม่สามารถเชื่อมต่อกับ Neo4j ได้"
        )

        st.code(
            """
[neo4j]
uri = "neo4j+s://YOUR_INSTANCE.databases.neo4j.io"
username = "YOUR_USERNAME"
password = "YOUR_PASSWORD"
database = "neo4j"
            """,
            language="toml",
        )

        st.error(str(e))

        return False


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("🐾 Pet Recommendation")

st.sidebar.write(
    "ระบบแนะนำสัตว์เลี้ยงด้วย Neo4j"
)

st.sidebar.divider()

page = st.sidebar.radio(
    "เมนู",
    [
        "Dashboard",
        "Pet Recommendation",
        "Pet Search",
        "Pet Database",
        "Graph Explorer",
        "Admin / Setup",
    ],
)

st.sidebar.divider()

st.sidebar.caption(
    "Neo4j + Streamlit"
)


# =========================================================
# DASHBOARD
# =========================================================

if page == "Dashboard":

    st.markdown(
        """
        <div class="hero">

        <h1>🐾 Pet Recommendation System</h1>

        <p>
        ระบบแนะนำสัตว์เลี้ยงโดยใช้ Neo4j Graph Database
        </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.header("📊 Dashboard")

    if not check_connection():
        st.stop()

    try:

        metrics = get_dashboard_metrics()

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "🐾 สัตว์เลี้ยง",
                metrics["pets"],
            )

        with col2:

            st.metric(
                "🏠 พื้นที่",
                metrics["spaces"],
            )

        with col3:

            st.metric(
                "🔗 Relationships",
                metrics["relationships"],
            )

    except Exception as e:

        st.error(
            "ไม่สามารถโหลด Dashboard ได้"
        )

        st.exception(e)

    st.divider()

    st.subheader(
        "ระบบทำงานอย่างไร?"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown(
            """
            ### 🏠 1. พื้นที่

            เลือกพื้นที่ที่คุณอาศัยอยู่
            เช่น House หรือ Condo
            """
        )

    with col2:

        st.markdown(
            """
            ### 💰 2. งบประมาณ

            เลือกระดับงบประมาณ
            Low / Medium / High
            """
        )

    with col3:

        st.markdown(
            """
            ### ⏰ 3. เวลา

            ระบุเวลาที่สามารถดูแลสัตว์ได้
            """
        )


# =========================================================
# PET RECOMMENDATION
# =========================================================

elif page == "Pet Recommendation":

    st.title("🐾 Pet Recommendation")

    st.write(
        "กรอกข้อมูลของคุณเพื่อให้ระบบแนะนำสัตว์เลี้ยง"
    )

    st.info(
        "คะแนนเต็ม 3 คะแนน: "
        "พื้นที่ + งบประมาณ + เวลา"
    )

    # -----------------------------------------------------
    # FORM
    # -----------------------------------------------------

    with st.form("recommendation_form"):

        col1, col2, col3 = st.columns(3)

        with col1:

            space = st.selectbox(
                "🏠 พื้นที่อยู่อาศัย",
                [
                    "House",
                    "Condo",
                    "Farm",
                    "Outdoor Space",
                ],
                format_func=lambda x: {
                    "House": "บ้าน (House)",
                    "Condo": "คอนโด (Condo)",
                    "Farm": "ฟาร์ม (Farm)",
                    "Outdoor Space": "พื้นที่กลางแจ้ง",
                }[x],
            )

        with col2:

            budget = st.selectbox(
                "💰 งบประมาณ",
                [
                    "Low",
                    "Medium",
                    "High",
                ],
                format_func=lambda x: {
                    "Low": "ต่ำ",
                    "Medium": "ปานกลาง",
                    "High": "สูง",
                }[x],
            )

        with col3:

            time = st.selectbox(
                "⏰ เวลาที่มี",
                [
                    "Low",
                    "Medium",
                    "High",
                ],
                format_func=lambda x: {
                    "Low": "น้อย",
                    "Medium": "ปานกลาง",
                    "High": "มาก",
                }[x],
            )

        submitted = st.form_submit_button(
            "🔍 แนะนำสัตว์เลี้ยง",
            type="primary",
            use_container_width=True,
        )

    # -----------------------------------------------------
    # RESULT
    # -----------------------------------------------------

    if submitted:

        if not check_connection():
            st.stop()

        try:

            results = recommend_pets(
                space=space,
                budget=budget,
                time=time,
            )

            st.divider()

            st.subheader(
                "🎯 ผลการแนะนำ"
            )

            if not results:

                st.warning(
                    "ไม่พบข้อมูลสัตว์เลี้ยง"
                )

            else:

                for pet in results:

                    score = pet["score"]

                    with st.container(
                        border=True
                    ):

                        col1, col2 = st.columns(
                            [4, 1]
                        )

                        with col1:

                            st.subheader(
                                f"🐾 {pet['name']}"
                            )

                            st.write(
                                pet["description"]
                            )

                            st.write(
                                f"**ขนาด:** "
                                f"{pet['size']}"
                            )

                            st.write(
                                f"**ระดับกิจกรรม:** "
                                f"{pet['activity_level']}"
                            )

                            spaces = (
                                pet.get("spaces")
                                or []
                            )

                            st.write(
                                "**พื้นที่ที่เหมาะสม:** "
                                + ", ".join(spaces)
                            )

                            st.write(
                                f"**งบประมาณ:** "
                                f"{pet.get('budget', '-')}"
                            )

                            st.write(
                                f"**เวลาที่ต้องใช้:** "
                                f"{pet.get('time', '-')}"
                            )

                        with col2:

                            st.metric(
                                "คะแนน",
                                f"{score}/3",
                            )

                            if score == 3:

                                st.success(
                                    "ตรงครบ 3 ด้าน"
                                )

                            elif score == 2:

                                st.info(
                                    "ตรง 2 ด้าน"
                                )

                            elif score == 1:

                                st.warning(
                                    "ตรง 1 ด้าน"
                                )

                            else:

                                st.error(
                                    "ตรง 0 ด้าน"
                                )

        except Exception as e:

            st.error(
                "เกิดข้อผิดพลาดในการแนะนำ"
            )

            st.exception(e)


# =========================================================
# PET SEARCH
# =========================================================

elif page == "Pet Search":

    st.title("🔎 Pet Search")

    st.write(
        "ค้นหาสัตว์เลี้ยงจากชื่อหรือคำอธิบาย"
    )

    keyword = st.text_input(
        "ค้นหา",
        placeholder="เช่น Dog, Cat, quiet",
    )

    if st.button(
        "🔍 ค้นหา",
        type="primary",
    ):

        if not check_connection():
            st.stop()

        try:

            results = search_pets(
                keyword
            )

            if not results:

                st.warning(
                    "ไม่พบข้อมูล"
                )

            else:

                st.success(
                    f"พบ {len(results)} รายการ"
                )

                for pet in results:

                    with st.container(
                        border=True
                    ):

                        st.subheader(
                            f"🐾 {pet['name']}"
                        )

                        st.write(
                            pet["description"]
                        )

                        col1, col2 = st.columns(2)

                        with col1:

                            st.write(
                                f"**ขนาด:** "
                                f"{pet['size']}"
                            )

                        with col2:

                            st.write(
                                f"**กิจกรรม:** "
                                f"{pet['activity_level']}"
                            )

        except Exception as e:

            st.error(
                "เกิดข้อผิดพลาดในการค้นหา"
            )

            st.exception(e)


# =========================================================
# PET DATABASE
# =========================================================

elif page == "Pet Database":

    st.title("📋 Pet Database")

    st.write(
        "ข้อมูลสัตว์เลี้ยงทั้งหมดใน Neo4j"
    )

    if st.button(
        "📥 โหลดข้อมูล",
        type="primary",
    ):

        if not check_connection():
            st.stop()

        try:

            pets = get_all_pets()

            if not pets:

                st.warning(
                    "ยังไม่มีข้อมูล"
                )

            else:

                rows = []

                for pet in pets:

                    rows.append(
                        {
                            "Pet": pet["name"],
                            "Description": pet[
                                "description"
                            ],
                            "Size": pet["size"],
                            "Activity": pet[
                                "activity_level"
                            ],
                            "Suitable Space": ", ".join(
                                pet.get("spaces") or []
                            ),
                            "Care": pet.get(
                                "care"
                            ),
                            "Budget": pet.get(
                                "budget"
                            ),
                            "Time": pet.get(
                                "time"
                            ),
                        }
                    )

                df = pd.DataFrame(rows)

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                )

        except Exception as e:

            st.error(
                "ไม่สามารถโหลดข้อมูลได้"
            )

            st.exception(e)


# =========================================================
# GRAPH EXPLORER
# =========================================================

elif page == "Graph Explorer":

    st.title("🕸️ Graph Explorer")

    st.write(
        "ดูความสัมพันธ์ระหว่าง Pet และข้อมูลต่าง ๆ"
    )

    if st.button(
        "🔗 โหลด Graph",
        type="primary",
    ):

        if not check_connection():
            st.stop()

        try:

            rows = get_pet_relationships()

            if not rows:

                st.warning(
                    "ไม่พบ Relationship"
                )

            else:

                st.success(
                    f"พบ {len(rows)} relationships"
                )

                # -----------------------------------------
                # TABLE
                # -----------------------------------------

                table_rows = []

                for row in rows:

                    table_rows.append(
                        {
                            "Pet": row[
                                "source_name"
                            ],
                            "Relationship": row[
                                "relationship"
                            ],
                            "Target": row[
                                "target_name"
                            ],
                            "Target Type": row[
                                "target_label"
                            ],
                        }
                    )

                df = pd.DataFrame(
                    table_rows
                )

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                )

                # -----------------------------------------
                # GRAPHVIZ
                # -----------------------------------------

                dot = [
                    "digraph G {",
                    'rankdir="LR";',
                    'node [shape=box];',
                ]

                used_nodes = set()

                for row in rows:

                    source_id = str(
                        row["source_id"]
                    )

                    target_id = str(
                        row["target_id"]
                    )

                    source_name = str(
                        row["source_name"]
                    ).replace(
                        '"',
                        "'",
                    )

                    target_name = str(
                        row["target_name"]
                    ).replace(
                        '"',
                        "'",
                    )

                    relationship = str(
                        row["relationship"]
                    )

                    if source_id not in used_nodes:

                        dot.append(
                            f'"{source_id}" '
                            f'[label="{source_name}"];'
                        )

                        used_nodes.add(
                            source_id
                        )

                    if target_id not in used_nodes:

                        dot.append(
                            f'"{target_id}" '
                            f'[label="{target_name}"];'
                        )

                        used_nodes.add(
                            target_id
                        )

                    dot.append(
                        f'"{source_id}" '
                        f'-> "{target_id}" '
                        f'[label="{relationship}"];'
                    )

                dot.append("}")

                st.subheader(
                    "Graph"
                )

                st.graphviz_chart(
                    "\n".join(dot),
                    use_container_width=True,
                )

        except Exception as e:

            st.error(
                "ไม่สามารถโหลด Graph ได้"
            )

            st.exception(e)


# =========================================================
# ADMIN / SETUP
# =========================================================

elif page == "Admin / Setup":

    st.title("⚙️ Admin / Setup")

    st.write(
        "หน้านี้ใช้สร้างข้อมูลเริ่มต้นใน Neo4j"
    )

    st.warning(
        "กดปุ่มด้านล่างเพื่อสร้าง Pet, "
        "LivingSpace, CareLevel, Budget, "
        "TimeAvailable และ Relationships"
    )

    # -----------------------------------------------------
    # TEST CONNECTION
    # -----------------------------------------------------

    st.subheader(
        "1. ตรวจสอบ Neo4j"
    )

    if st.button(
        "🔌 Test Neo4j Connection"
    ):

        try:

            if ping():

                st.success(
                    "เชื่อมต่อ Neo4j สำเร็จ ✅"
                )

            else:

                st.error(
                    "Neo4j ไม่ตอบกลับ"
                )

        except Exception as e:

            st.error(
                "เชื่อมต่อ Neo4j ไม่สำเร็จ"
            )

            st.exception(e)

    st.divider()

    # -----------------------------------------------------
    # SEED DATA
    # -----------------------------------------------------

    st.subheader(
        "2. สร้างข้อมูลระบบ"
    )

    if st.button(
        "🚀 Create Pet Database",
        type="primary",
        use_container_width=True,
    ):

        if not check_connection():
            st.stop()

        try:

            with st.spinner(
                "กำลังสร้างข้อมูลใน Neo4j..."
            ):

                seed_demo_data()

            st.success(
                "สร้างฐานข้อมูลสำเร็จแล้ว ✅"
            )

            st.balloons()

        except Exception as e:

            st.error(
                "สร้างฐานข้อมูลไม่สำเร็จ"
            )

            st.exception(e)

    st.divider()

    st.subheader(
        "Graph Schema"
    )

    st.code(
        """
(:Pet)
    |
    |--[:SUITABLE_FOR]--> (:LivingSpace)
    |
    |--[:REQUIRES]------> (:CareLevel)
    |
    |--[:COST_LEVEL]----> (:Budget)
    |
    |--[:NEEDS_TIME]----> (:TimeAvailable)
        """,
        language="text",
    )