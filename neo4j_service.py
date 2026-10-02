from __future__ import annotations

from typing import Any

import streamlit as st
from neo4j import GraphDatabase, RoutingControl


# ==========================================
# NEO4J CONFIGURATION
# ==========================================

def _config() -> tuple[str, str, str, str]:
    cfg = st.secrets["neo4j"]

    return (
        cfg["uri"],
        cfg["username"],
        cfg["password"],
        cfg.get("database", "neo4j"),
    )


@st.cache_resource(show_spinner=False)
def get_driver():
    """สร้าง Neo4j Driver สำหรับใช้งานร่วมกันใน Streamlit"""
    uri, username, password, _ = _config()

    driver = GraphDatabase.driver(
        uri,
        auth=(username, password),
    )

    driver.verify_connectivity()
    return driver


def query(
    cypher: str,
    parameters: dict[str, Any] | None = None,
    *,
    write: bool = False,
) -> list[dict[str, Any]]:
    """ส่ง Cypher Query ไปยัง Neo4j และคืนผลลัพธ์เป็น list"""
    _, _, _, database = _config()

    records, _, _ = get_driver().execute_query(
        cypher,
        parameters_=parameters or {},
        database_=database,
        routing_=(
            RoutingControl.WRITE if write
            else RoutingControl.READ
        ),
    )

    return [record.data() for record in records]


def ping() -> bool:
    """ตรวจสอบว่า Neo4j เชื่อมต่อได้หรือไม่"""
    rows = query("RETURN 1 AS ok")
    return bool(rows and rows[0]["ok"] == 1)


# ==========================================
# CREATE SCHEMA
# ==========================================

def create_schema() -> None:
    """สร้าง Constraint ป้องกันชื่อสัตว์ซ้ำ"""
    query(
        """
        CREATE CONSTRAINT pet_name_unique IF NOT EXISTS
        FOR (p:Pet)
        REQUIRE p.name IS UNIQUE
        """,
        write=True,
    )

    supporting_nodes = [
        ("LivingSpace", "living_space_name_unique"),
        ("CareLevel", "care_level_name_unique"),
        ("Budget", "budget_name_unique"),
        ("TimeAvailable", "time_available_name_unique"),
    ]

    for label, constraint_name in supporting_nodes:
        query(
            f"""
            CREATE CONSTRAINT {constraint_name} IF NOT EXISTS
            FOR (n:{label})
            REQUIRE n.name IS UNIQUE
            """,
            write=True,
        )


# ==========================================
# SEED DEMO DATA
# ==========================================

def seed_demo_data() -> None:
    """สร้างข้อมูลสัตว์เลี้ยงและข้อมูลสำหรับระบบแนะนำ"""

    create_schema()

    pets = [
        {
            "name": "Dog",
            "description": "Friendly and social companion",
            "size": "Medium",
            "activity_level": "High",
            "spaces": ["House"],
            "care": "High",
            "budget": "Medium",
            "time": "High",
        },
        {
            "name": "Cat",
            "description": "Independent and adaptable companion",
            "size": "Small",
            "activity_level": "Medium",
            "spaces": ["House", "Condo"],
            "care": "Medium",
            "budget": "Medium",
            "time": "Medium",
        },
        {
            "name": "Bird",
            "description": "Small companion that can be social and active",
            "size": "Small",
            "activity_level": "Medium",
            "spaces": ["Condo", "House"],
            "care": "Low",
            "budget": "Medium",
            "time": "Medium",
        },
        {
            "name": "Rabbit",
            "description": "Gentle and quiet small companion",
            "size": "Small",
            "activity_level": "Medium",
            "spaces": ["Condo", "House"],
            "care": "Medium",
            "budget": "Medium",
            "time": "Medium",
        },
        {
            "name": "Fish",
            "description": "Quiet aquatic pet that needs an aquarium",
            "size": "Small",
            "activity_level": "Low",
            "spaces": ["Condo", "House"],
            "care": "Low",
            "budget": "Low",
            "time": "Low",
        },
        {
            "name": "Hamster",
            "description": "Small and easy-to-observe companion",
            "size": "Small",
            "activity_level": "Medium",
            "spaces": ["Condo", "House"],
            "care": "Low",
            "budget": "Low",
            "time": "Medium",
        },
        {
            "name": "Duck",
            "description": "Social bird that needs outdoor space",
            "size": "Medium",
            "activity_level": "Medium",
            "spaces": ["Farm", "Outdoor Space"],
            "care": "Medium",
            "budget": "Medium",
            "time": "Medium",
        },
        {
            "name": "Sheep",
            "description": "Social farm animal that needs outdoor space",
            "size": "Large",
            "activity_level": "Medium",
            "spaces": ["Farm", "Outdoor Space"],
            "care": "Medium",
            "budget": "High",
            "time": "High",
        },
        {
            "name": "Turtle",
            "description": "Quiet and long-lived companion",
            "size": "Small",
            "activity_level": "Low",
            "spaces": ["Condo", "House"],
            "care": "Low",
            "budget": "Low",
            "time": "Low",
        },
        {
            "name": "Horse",
            "description": "Large active animal that needs significant space",
            "size": "Large",
            "activity_level": "High",
            "spaces": ["Farm", "Outdoor Space"],
            "care": "High",
            "budget": "High",
            "time": "High",
        },
    ]

    # สร้างโหนดประเภทพื้นที่และระดับต่าง ๆ
    query(
        """
        UNWIND $spaces AS name
        MERGE (:LivingSpace {name: name})
        """,
        {"spaces": ["House", "Condo", "Farm", "Outdoor Space"]},
        write=True,
    )

    query(
        """
        UNWIND $levels AS name
        MERGE (:CareLevel {name: name})
        """,
        {"levels": ["Low", "Medium", "High"]},
        write=True,
    )

    query(
        """
        UNWIND $levels AS name
        MERGE (:Budget {name: name})
        """,
        {"levels": ["Low", "Medium", "High"]},
        write=True,
    )

    query(
        """
        UNWIND $levels AS name
        MERGE (:TimeAvailable {name: name})
        """,
        {"levels": ["Low", "Medium", "High"]},
        write=True,
    )

    # สร้างข้อมูลสัตว์เลี้ยง
    query(
        """
        UNWIND $pets AS pet
        MERGE (p:Pet {name: pet.name})
        SET p.description = pet.description,
            p.size = pet.size,
            p.activity_level = pet.activity_level
        """,
        {"pets": pets},
        write=True,
    )

    # สร้างความสัมพันธ์ระหว่างสัตว์เลี้ยงกับข้อมูลประกอบ
    query(
        """
        UNWIND $pets AS pet
        MATCH (p:Pet {name: pet.name})
        MATCH (care:CareLevel {name: pet.care})
        MATCH (budget:Budget {name: pet.budget})
        MATCH (time:TimeAvailable {name: pet.time})

        MERGE (p)-[:REQUIRES]->(care)
        MERGE (p)-[:COST_LEVEL]->(budget)
        MERGE (p)-[:NEEDS_TIME]->(time)

        WITH p, pet
        UNWIND pet.spaces AS space_name
        MATCH (space:LivingSpace {name: space_name})
        MERGE (p)-[:SUITABLE_FOR]->(space)
        """,
        {"pets": pets},
        write=True,
    )


# ==========================================
# PET SEARCH
# ==========================================

def get_all_pets() -> list[dict[str, Any]]:
    """ดึงข้อมูลสัตว์เลี้ยงทั้งหมด"""
    return query(
        """
        MATCH (p:Pet)
        OPTIONAL MATCH (p)-[:SUITABLE_FOR]->(s:LivingSpace)
        OPTIONAL MATCH (p)-[:REQUIRES]->(c:CareLevel)
        OPTIONAL MATCH (p)-[:COST_LEVEL]->(b:Budget)
        OPTIONAL MATCH (p)-[:NEEDS_TIME]->(t:TimeAvailable)

        RETURN
            p.name AS name,
            p.description AS description,
            p.size AS size,
            p.activity_level AS activity_level,
            collect(DISTINCT s.name) AS spaces,
            collect(DISTINCT c.name)[0] AS care,
            collect(DISTINCT b.name)[0] AS budget,
            collect(DISTINCT t.name)[0] AS time

        ORDER BY p.name
        """
    )


def search_pets(keyword: str = "") -> list[dict[str, Any]]:
    """ค้นหาสัตว์จากชื่อหรือคำอธิบาย"""
    return query(
        """
        MATCH (p:Pet)
        WHERE $keyword = ""
           OR toLower(p.name) CONTAINS toLower($keyword)
           OR toLower(p.description) CONTAINS toLower($keyword)

        RETURN
            p.name AS name,
            p.description AS description,
            p.size AS size,
            p.activity_level AS activity_level

        ORDER BY p.name
        """,
        {"keyword": keyword.strip()},
    )


# ==========================================
# PET RECOMMENDATION
# ==========================================

def recommend_pets(
    space: str,
    budget: str,
    time: str,
) -> list[dict[str, Any]]:
    """
    แนะนำสัตว์เลี้ยงด้วยคะแนน 3 ด้าน
    - พื้นที่อยู่อาศัย
    - งบประมาณ
    - เวลาที่มี
    คะแนนเต็ม 3 คะแนน
    """

    return query(
        """
        MATCH (p:Pet)
        OPTIONAL MATCH (p)-[:SUITABLE_FOR]->(s:LivingSpace)
        OPTIONAL MATCH (p)-[:COST_LEVEL]->(b:Budget)
        OPTIONAL MATCH (p)-[:NEEDS_TIME]->(t:TimeAvailable)

        WITH
            p,
            collect(DISTINCT s.name) AS spaces,
            collect(DISTINCT b.name)[0] AS pet_budget,
            collect(DISTINCT t.name)[0] AS pet_time

        WITH
            p,
            spaces,
            pet_budget,
            pet_time,
            CASE
                WHEN $space IN spaces THEN 1
                ELSE 0
            END +
            CASE
                WHEN pet_budget = $budget THEN 1
                ELSE 0
            END +
            CASE
                WHEN pet_time = $time THEN 1
                ELSE 0
            END AS score

        RETURN
            p.name AS name,
            p.description AS description,
            p.size AS size,
            p.activity_level AS activity_level,
            spaces,
            pet_budget AS budget,
            pet_time AS time,
            score

        ORDER BY score DESC, name
        """,
        {
            "space": space,
            "budget": budget,
            "time": time,
        },
    )


# ==========================================
# GRAPH EXPLORER
# ==========================================

def get_pet_relationships() -> list[dict[str, Any]]:
    """ดึงความสัมพันธ์ทั้งหมดสำหรับแสดงกราฟ"""
    return query(
        """
        MATCH (p:Pet)-[r]->(n)
        RETURN
            elementId(p) AS source_id,
            p.name AS source_name,
            labels(p)[0] AS source_label,
            type(r) AS relationship,
            elementId(n) AS target_id,
            coalesce(n.name, 'Unknown') AS target_name,
            labels(n)[0] AS target_label
        ORDER BY p.name, type(r), target_name
        """
    )


def get_dashboard_metrics() -> dict[str, int]:
    """ดึงจำนวนข้อมูลสำหรับหน้า Dashboard"""
    rows = query(
        """
        MATCH (p:Pet)
        WITH count(p) AS pets
        MATCH (s:LivingSpace)
        WITH pets, count(s) AS spaces
        MATCH ()-[r]->()
        RETURN
            pets,
            spaces,
            count(r) AS relationships
        """
    )

    if not rows:
        return {"pets": 0, "spaces": 0, "relationships": 0}

    return rows[0]