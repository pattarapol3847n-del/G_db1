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


# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Pet Recommendation System",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==========================================
# CUSTOM CSS
# ==========================================

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    .hero {
        padding: 1.7rem;
        border-radius: 18px;
        background: linear-gradient(
            120deg,
            #164e63 0%,
            #0f766e 55%,
            #65a30d 100%
        );
        color: white;
        margin-bottom: 1.2rem;
    }

    .hero h1 {
        margin: 0;
        font-size: 2.3rem;
    }

    .hero p {
        margin-top: 0.5rem;
        font-size: 1rem;
    }

    .pet-card {
        padding: 1.1rem;
        border: 1px solid rgba(128, 128, 128, 0.3);
        border-radius: 16px;
        margin-bottom: 0.8rem;
    }

    .score {
        display: inline-block;
        padding: 0.3rem 0.7rem;
        border-radius: 999px;
        background: #0f766e;
        color: white;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==========================================
# CONNECTION CHECK
# ==========================================

def require_connection() -> None:
    try:
        if not ping():
            raise RuntimeError("Neo4j did not return a healthy response")

    except Exception as exc:
        st.error("ไม่สามารถเชื่อมต่อ Neo4j Aura ได้")

        st.markdown("ตรวจสอบไฟล์ `.streamlit/secrets.toml`")
        st.code(
            '[neo4j]\n'
            'uri = "neo4j+s://YOUR_INSTANCE.databases.neo4j.io"\n'
            'username = "YOUR_USERNAME"\n'
            'password = "YOUR_PASSWORD"\n'
            'database = "neo4j"',
            language="toml",
        )

        st.caption(
            "ตรวจสอบ URI, username, password และชื่อ database "
            "ให้ตรงกับ Neo4j Aura ของคุณ"
        )
        st.exception(exc)
        st.stop()


# ==========================================
# SIDEBAR NAVIGATION
# ==========================================

st.sidebar.title("🐾 Pet Recommendation")
st.sidebar.caption("ระบบแนะนำสัตว์เลี้ยงด้วย Neo4j")

page = st.sidebar.radio(
    "เมนูหลัก",
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
st.sidebar.caption("Pet Recommendation System")


# ==========================================
# HOME / DASHBOARD
# ==========================================

if page == "Dashboard":

    st.markdown(
        """
        <div class="hero">
            <h1>🐾 Pet Recommendation System</h1>
            <p>
                ค้นหาสัตว์เลี้ยงที่เหมาะกับพื้นที่อยู่อาศัย
                งบประมาณ และเวลาที่คุณมี
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("📊 ภาพรวมระบบ")

    try:
        require_connection()
        metrics = get_dashboard_metrics()

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "จำนวนสัตว์เลี้ยง",
            metrics["pets"],
        )

        col2.metric(
            "ประเภทพื้นที่อยู่อาศัย",
            metrics["spaces"],
        )

        col3.metric(
            "ความสัมพันธ์ในกราฟ",
            metrics["relationships"],
        )

    except Exception as exc:
        st.error("ไม่สามารถโหลดข้อมูล Dashboard ได้")
        st.exception(exc)

    st.divider()

    st.subheader("💡 วิธีใช้งาน")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 1. 🏠")
        st.write("เลือกพื้นที่อยู่อาศัยที่คุณมี")

    with col2:
        st.markdown("### 2. 💰")
        st.write("ระบุงบประมาณและเวลาที่สามารถดูแลสัตว์เลี้ยง")

    with col3:
        st.markdown("### 3. 🐶")
        st.write("ระบบคำนวณคะแนนและแนะนำสัตว์เลี้ยงให้คุณ")


# ==========================================
# PET RECOMMENDATION
# ==========================================

elif page == "Pet Recommendation":

    st.title("🐾 Pet Recommendation")
    st.write(
        "เลือกข้อมูลของคุณเพื่อค้นหาสัตว์เลี้ยงที่เหมาะสม"
    )

    st.info(
        "ระบบจะให้คะแนนจาก 3 ด้าน ได้แก่ พื้นที่ งบประมาณ "
        "และเวลาที่มี คะแนนเต็ม 3 คะแนน"
    )

    with st.form("recommendation_form"):

        col1, col2, col3 = st.columns(3)

        with col1:
            user_space = st.selectbox(
                "🏠 พื้นที่อยู่อาศัย",
                [
                    "House",
                    "Condo",
                    "Farm",
                    "Outdoor Space",
                ],
                format_func=lambda x: {
                    "House": "บ้าน",
                    "Condo": "คอนโด",
                    "Farm": "ฟาร์ม",
                    "Outdoor Space": "พื้นที่กลางแจ้ง",
                }[x],
            )

        with col2:
            user_budget = st.selectbox(
                "💰 งบประมาณ",
                ["Low", "Medium", "High"],
                format_func=lambda x: {
                    "Low": "ต่ำ",
                    "Medium": "ปานกลาง",
                    "High": "สูง",
                }[x],
            )

        with col3:
            user_time = st.selectbox(
                "⏰ เวลาที่มีสำหรับดูแลสัตว์",
                ["Low", "Medium", "High"],
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

    if submitted:
        try:
            require_connection()

            results = recommend_pets(
                space=user_space,
                budget=user_budget,
                time=user_time,
            )

            st.divider()
            st.subheader("🎯 ผลการแนะนำสัตว์เลี้ยง")

            if not results:
                st.warning("ไม่พบข้อมูลสัตว์เลี้ยงในระบบ")
            else:
                top_score = max(row["score"] for row in results)

                st.success(
                    f"ระบบพบสัตว์เลี้ยง {len(results)} ประเภท "
                    f"โดยคะแนนสูงสุดคือ {top_score}/3"
                )

                for pet in results:
                    with st.container(border=True):
                        col1, col2 = st.columns([4, 1])

                        with col1:
                            st.subheader(
                                f"🐾 {pet['name']}"
                            )
                            st.write(pet["description"])

                            st.caption(
                                f"ขนาด: {pet['size']} | "
                                f"กิจกรรม: {pet['activity_level']}"
                            )

                            spaces = pet.get("spaces") or []

                            st.write(
                                "**พื้นที่ที่เหมาะสม:** "
                                + (
                                    ", ".join(spaces)
                                    if spaces
                                    else "ไม่มีข้อมูล"
                                )
                            )

                            st.write(
                                f"**งบประมาณ:** {pet.get('budget') or '-'}"
                            )
                            st.write(
                                f"**เวลาที่ต้องใช้:** {pet.get('time') or '-'}"
                            )

                        with col2:
                            st.metric(
                                "คะแนน",
                                f"{pet['score']}/3",
                            )

                            if pet["score"] == 3:
                                st.success("ตรงครบทุกด้าน")
                            elif pet["score"] == 2:
                                st.info("ตรง 2 ด้าน")
                            elif pet["score"] == 1:
                                st.warning("ตรง 1 ด้าน")
                            else:
                                st.caption("ตรง 0 ด้าน")

                st.caption(
                    "หมายเหตุ: คะแนนเป็นการจับคู่ข้อมูลเบื้องต้น "
                    "ควรศึกษาความต้องการในการเลี้ยงจริงก่อนตัดสินใจ"
                )

        except Exception as exc:
            st.error("เกิดข้อผิดพลาดในการแนะนำสัตว์เลี้ยง")
            st.exception(exc)


# ==========================================
# PET SEARCH
# ==========================================

elif page == "Pet Search":

    st.title("🔎 ค้นหาสัตว์เลี้ยง")
    st.write("ค้นหาจากชื่อสัตว์เลี้ยงหรือคำอธิบาย")

    keyword = st.text_input(
        "คำค้นหา",
        placeholder="เช่น Dog, Cat, quiet, active",
    )

    if st.button("ค้นหา", type="primary"):
        try:
            require_connection()
            results = search_pets(keyword)

            if not results:
                st.warning("ไม่พบสัตว์เลี้ยงที่ตรงกับคำค้นหา")
            else:
                st.success(f"พบข้อมูล {len(results)} รายการ")

                for pet in results:
                    with st.container(border=True):
                        st.subheader(f"🐾 {pet['name']}")
                        st.write(pet["description"])

                        col1, col2 = st.columns(2)

                        col1.write(
                            f"**ขนาด:** {pet['size']}"
                        )
                        col2.write(
                            f"**ระดับกิจกรรม:** {pet['activity_level']}"
                        )

        except Exception as exc:
            st.error("ไม่สามารถค้นหาข้อมูลได้")
            st.exception(exc)


# ==========================================
# PET DATABASE
# ==========================================

elif page == "Pet Database":

    st.title("📋 ฐานข้อมูลสัตว์เลี้ยง")
    st.write("รายการสัตว์เลี้ยงและคุณสมบัติที่อยู่ใน Neo4j")

    if st.button("โหลดข้อมูลทั้งหมด", type="primary"):
        try:
            require_connection()
            pets = get_all_pets()

            if not pets:
                st.warning(
                    "ยังไม่มีข้อมูล กรุณาไปที่ Admin / Setup "
                    "เพื่อสร้างข้อมูลตัวอย่าง"
                )
            else:
                df = pd.DataFrame(pets)

                df = df.rename(
                    columns={
                        "name": "ชื่อสัตว์",
                        "description": "คำอธิบาย",
                        "size": "ขนาด",
                        "activity_level": "ระดับกิจกรรม",
                        "spaces": "พื้นที่ที่เหมาะสม",
                        "care": "ระดับการดูแล",
                        "budget": "งบประมาณ",
                        "time": "เวลาที่ต้องใช้",
                    }
                )

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                )

        except Exception as exc:
            st.error("ไม่สามารถโหลดฐานข้อมูลสัตว์เลี้ยงได้")
            st.exception(exc)


# ==========================================
# GRAPH EXPLORER
# ==========================================

elif page == "Graph Explorer":

    st.title("🕸️ Graph Explorer")
    st.write(
        "แสดงความสัมพันธ์ระหว่างสัตว์เลี้ยงกับพื้นที่ "
        "งบประมาณ เวลา และระดับการดูแล"
    )

    if st.button("โหลดความสัมพันธ์", type="primary"):
        try:
            require_connection()
            rows = get_pet_relationships()

            if not rows:
                st.warning(
                    "ยังไม่มีความสัมพันธ์ กรุณาสร้างข้อมูลใน Admin / Setup"
                )
            else:
                st.success(
                    f"พบความสัมพันธ์ทั้งหมด {len(rows)} รายการ"
                )

                df = pd.DataFrame(rows)

                st.dataframe(
                    df[
                        [
                            "source_name",
                            "source_label",
                            "relationship",
                            "target_name",
                            "target_label",
                        ]
                    ].rename(
                        columns={
                            "source_name": "ต้นทาง",
                            "source_label": "ประเภทต้นทาง",
                            "relationship": "ความสัมพันธ์",
                            "target_name": "ปลายทาง",
                            "target_label": "ประเภทปลายทาง",
                        }
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

                dot = [
                    "digraph G {",
                    'rankdir="LR";',
                    (
                        'node [shape=box, style="rounded,filled", '
                        'fillcolor="#ecfeff", color="#0f766e"];'
                    ),
                ]

                seen_nodes = set()

                for row in rows:
                    source_id = str(row["source_id"])
                    target_id = str(row["target_id"])

                    source_name = str(row["source_name"]).replace(
                        '"', "'"
                    )
                    target_name = str(row["target_name"]).replace(
                        '"', "'"
                    )

                    source_label = str(row["source_label"])
                    target_label = str(row["target_label"])
                    relationship = str(row["relationship"])

                    if source_id not in seen_nodes:
                        dot.append(
                            f'"{source_id}" '
                            f'[label="{source_name}\\n:{source_label}"];'
                        )
                        seen_nodes.add(source_id)

                    if target_id not in seen_nodes:
                        dot.append(
                            f'"{target_id}" '
                            f'[label="{target_name}\\n:{target_label}"];'
                        )
                        seen_nodes.add(target_id)

                    dot.append(
                        f'"{source_id}" -> "{target_id}" '
                        f'[label="{relationship}"];'
                    )

                dot.append("}")

                st.subheader("แผนภาพความสัมพันธ์")
                st.graphviz_chart(
                    "\n".join(dot),
                    use_container_width=True,
                )

        except Exception as exc:
            st.error("ไม่สามารถโหลดกราฟได้")
            st.exception(exc)


# ==========================================
# ADMIN / SETUP
# ==========================================

elif page == "Admin / Setup":

    st.title("⚙️ Admin / Setup")

    st.write(
        "ใช้สำหรับสร้างโครงสร้างและข้อมูลตัวอย่างใน Neo4j"
    )

    st.warning(
        "ระบบใช้ MERGE เพื่อสร้างหรืออัปเดตข้อมูลสัตว์เลี้ยง "
        "โดยไม่ลบข้อมูลเดิม"
    )

    st.markdown(
        """
        **Graph Schema**

        - `(:Pet)-[:SUITABLE_FOR]->(:LivingSpace)`
        - `(:Pet)-[:REQUIRES]->(:CareLevel)`
        - `(:Pet)-[:COST_LEVEL]->(:Budget)`
        - `(:Pet)-[:NEEDS_TIME]->(:TimeAvailable)`
        """
    )

    st.divider()

    if st.button(
        "🚀 สร้างข้อมูลและความสัมพันธ์",
        type="primary",
        use_container_width=True,
    ):
        try:
            require_connection()

            with st.spinner("กำลังสร้างข้อมูลใน Neo4j..."):
                seed_demo_data()

            st.success(
                "สร้างข้อมูลสัตว์เลี้ยงและความสัมพันธ์สำเร็จแล้ว"
            )

            st.balloons()

        except Exception as exc:
            st.error("สร้างข้อมูลไม่สำเร็จ")
            st.exception(exc)

    st.divider()

    if st.button("ตรวจสอบการเชื่อมต่อ Neo4j"):
        try:
            if ping():
                st.success("เชื่อมต่อ Neo4j สำเร็จ")
            else:
                st.error("Neo4j ไม่ตอบกลับตามที่คาดไว้")

        except Exception as exc:
            st.error("เชื่อมต่อ Neo4j ไม่สำเร็จ")
            st.exception(exc)