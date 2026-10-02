# neo4j_service.py

from __future__ import annotations

from typing import Any

import streamlit as st
from neo4j import GraphDatabase


# =========================================================
# NEO4J CONFIG
# =========================================================

def _get_config():
    """
    อ่านค่าการเชื่อมต่อ Neo4j จาก Streamlit Secrets
    """

    if "neo4j" not in st.secrets:
        raise RuntimeError(
            "ไม่พบ [neo4j] ใน Streamlit Secrets"
        )

    config = st.secrets["neo4j"]

    uri = config.get("uri")
    username = config.get("username")
    password = config.get("password")
    database = config.get("database", "neo4j")

    if not uri:
        raise RuntimeError("ไม่พบ neo4j.uri")

    if not username:
        raise RuntimeError("ไม่พบ neo4j.username")

    if not password:
        raise RuntimeError("ไม่พบ neo4j.password")

    return uri, username, password, database


# =========================================================
# NEO4J DRIVER
# =========================================================

@st.cache_resource
def get_driver():
    """
    สร้าง Neo4j Driver
    """

    uri, username, password, _ = _get_config()

    driver = GraphDatabase.driver(
        uri,
        auth=(username, password),
    )

    # ตรวจสอบ connection
    driver.verify_connectivity()

    return driver


# =========================================================
# QUERY HELPER
# =========================================================

def query(
    cypher: str,
    parameters: dict[str, Any] | None = None,
):
    """
    Execute Cypher query และคืนค่าเป็น list ของ dictionary
    """

    _, _, _, database = _get_config()

    driver = get_driver()

    records, summary, keys = driver.execute_query(
        cypher,
        parameters_=(parameters or {}),
        database_=database,
    )

    return [record.data() for record in records]


# =========================================================
# PING
# =========================================================

def ping() -> bool:
    """
    ตรวจสอบว่า Neo4j เชื่อมต่อได้หรือไม่
    """

    try:
        result = query(
            """
            RETURN 1 AS ok
            """
        )

        return (
            len(result) > 0
            and result[0].get("ok") == 1
        )

    except Exception:
        return False


# =========================================================
# CREATE SCHEMA
# =========================================================

def create_schema():
    """
    สร้าง Unique Constraints
    """

    # Pet
    query(
        """
        CREATE CONSTRAINT pet_name_unique IF NOT EXISTS
        FOR (p:Pet)
        REQUIRE p.name IS UNIQUE
        """
    )

    # LivingSpace
    query(
        """
        CREATE CONSTRAINT living_space_name_unique IF NOT EXISTS
        FOR (n:LivingSpace)
        REQUIRE n.name IS UNIQUE
        """
    )

    # CareLevel
    query(
        """
        CREATE CONSTRAINT care_level_name_unique IF NOT EXISTS
        FOR (n:CareLevel)
        REQUIRE n.name IS UNIQUE
        """
    )

    # Budget
    query(
        """
        CREATE CONSTRAINT budget_name_unique IF NOT EXISTS
        FOR (n:Budget)
        REQUIRE n.name IS UNIQUE
        """
    )

    # TimeAvailable
    query(
        """
        CREATE CONSTRAINT time_available_name_unique IF NOT EXISTS
        FOR (n:TimeAvailable)
        REQUIRE n.name IS UNIQUE
        """
    )


# =========================================================
# SEED DATA
# =========================================================

def seed_demo_data():
    """
    สร้างข้อมูล Pet Recommendation System
    ตามข้อมูลจาก Colab
    """

    # -----------------------------------------------------
    # Schema
    # -----------------------------------------------------

    create_schema()

    # -----------------------------------------------------
    # PETS
    # -----------------------------------------------------

    pets = [
        {
            "name": "Dog",
            "description": "Friendly and social companion",
            "size": "Medium",
            "activity_level": "High",
        },
        {
            "name": "Cat",
            "description": "Independent and adaptable companion",
            "size": "Small",
            "activity_level": "Medium",
        },
        {
            "name": "Bird",
            "description": "Small companion that can be social and active",
            "size": "Small",
            "activity_level": "Medium",
        },
        {
            "name": "Rabbit",
            "description": "Gentle and quiet small companion",
            "size": "Small",
            "activity_level": "Medium",
        },
        {
            "name": "Fish",
            "description": "Quiet aquatic pet that needs an aquarium",
            "size": "Small",
            "activity_level": "Low",
        },
        {
            "name": "Hamster",
            "description": "Small and easy-to-observe companion",
            "size": "Small",
            "activity_level": "Medium",
        },
        {
            "name": "Duck",
            "description": "Social bird that needs outdoor space",
            "size": "Medium",
            "activity_level": "Medium",
        },
        {
            "name": "Sheep",
            "description": "Social farm animal that needs outdoor space",
            "size": "Large",
            "activity_level": "Medium",
        },
        {
            "name": "Turtle",
            "description": "Quiet and long-lived companion",
            "size": "Small",
            "activity_level": "Low",
        },
        {
            "name": "Horse",
            "description": "Large active animal that needs significant space",
            "size": "Large",
            "activity_level": "High",
        },
    ]

    query(
        """
        UNWIND $pets AS pet

        MERGE (p:Pet {name: pet.name})

        SET
            p.description = pet.description,
            p.size = pet.size,
            p.activity_level = pet.activity_level
        """,
        {
            "pets": pets
        },
    )

    # -----------------------------------------------------
    # LIVING SPACE
    # -----------------------------------------------------

    living_spaces = [
        "House",
        "Condo",
        "Farm",
        "Outdoor Space",
    ]

    query(
        """
        UNWIND $items AS item

        MERGE (:LivingSpace {name: item})
        """,
        {
            "items": living_spaces
        },
    )

    # -----------------------------------------------------
    # CARE LEVEL
    # -----------------------------------------------------

    care_levels = [
        "Low",
        "Medium",
        "High",
    ]

    query(
        """
        UNWIND $items AS item

        MERGE (:CareLevel {name: item})
        """,
        {
            "items": care_levels
        },
    )

    # -----------------------------------------------------
    # BUDGET
    # -----------------------------------------------------

    budgets = [
        "Low",
        "Medium",
        "High",
    ]

    query(
        """
        UNWIND $items AS item

        MERGE (:Budget {name: item})
        """,
        {
            "items": budgets
        },
    )

    # -----------------------------------------------------
    # TIME AVAILABLE
    # -----------------------------------------------------

    times = [
        "Low",
        "Medium",
        "High",
    ]

    query(
        """
        UNWIND $items AS item

        MERGE (:TimeAvailable {name: item})
        """,
        {
            "items": times
        },
    )

    # -----------------------------------------------------
    # PET RELATIONSHIPS
    # -----------------------------------------------------

    relationships = [
        {
            "pet": "Dog",
            "spaces": ["House"],
            "care": "High",
            "budget": "Medium",
            "time": "High",
        },
        {
            "pet": "Cat",
            "spaces": ["House", "Condo"],
            "care": "Medium",
            "budget": "Medium",
            "time": "Medium",
        },
        {
            "pet": "Bird",
            "spaces": ["Condo", "House"],
            "care": "Low",
            "budget": "Medium",
            "time": "Medium",
        },
        {
            "pet": "Rabbit",
            "spaces": ["Condo", "House"],
            "care": "Medium",
            "budget": "Medium",
            "time": "Medium",
        },
        {
            "pet": "Fish",
            "spaces": ["Condo", "House"],
            "care": "Low",
            "budget": "Low",
            "time": "Low",
        },
        {
            "pet": "Hamster",
            "spaces": ["Condo", "House"],
            "care": "Low",
            "budget": "Low",
            "time": "Medium",
        },
        {
            "pet": "Duck",
            "spaces": ["Farm", "Outdoor Space"],
            "care": "Medium",
            "budget": "Medium",
            "time": "Medium",
        },
        {
            "pet": "Sheep",
            "spaces": ["Farm", "Outdoor Space"],
            "care": "Medium",
            "budget": "High",
            "time": "High",
        },
        {
            "pet": "Turtle",
            "spaces": ["Condo", "House"],
            "care": "Low",
            "budget": "Low",
            "time": "Low",
        },
        {
            "pet": "Horse",
            "spaces": ["Farm", "Outdoor Space"],
            "care": "High",
            "budget": "High",
            "time": "High",
        },
    ]

    # -----------------------------------------------------
    # CREATE RELATIONSHIPS
    # -----------------------------------------------------

    for item in relationships:

        # Suitable spaces
        query(
            """
            MATCH (p:Pet {name: $pet})

            UNWIND $spaces AS space_name

            MATCH (s:LivingSpace {name: space_name})

            MERGE (p)-[:SUITABLE_FOR]->(s)
            """,
            {
                "pet": item["pet"],
                "spaces": item["spaces"],
            },
        )

        # Care
        query(
            """
            MATCH (p:Pet {name: $pet})
            MATCH (c:CareLevel {name: $care})

            MERGE (p)-[:REQUIRES]->(c)
            """,
            {
                "pet": item["pet"],
                "care": item["care"],
            },
        )

        # Budget
        query(
            """
            MATCH (p:Pet {name: $pet})
            MATCH (b:Budget {name: $budget})

            MERGE (p)-[:COST_LEVEL]->(b)
            """,
            {
                "pet": item["pet"],
                "budget": item["budget"],
            },
        )

        # Time
        query(
            """
            MATCH (p:Pet {name: $pet})
            MATCH (t:TimeAvailable {name: $time})

            MERGE (p)-[:NEEDS_TIME]->(t)
            """,
            {
                "pet": item["pet"],
                "time": item["time"],
            },
        )


# =========================================================
# GET ALL PETS
# =========================================================

def get_all_pets():
    """
    ดึงข้อมูลสัตว์เลี้ยงทั้งหมด
    """

    return query(
        """
        MATCH (p:Pet)

        OPTIONAL MATCH (p)-[:SUITABLE_FOR]->(s:LivingSpace)
        OPTIONAL MATCH (p)-[:REQUIRES]->(c:CareLevel)
        OPTIONAL MATCH (p)-[:COST_LEVEL]->(b:Budget)
        OPTIONAL MATCH (p)-[:NEEDS_TIME]->(t:TimeAvailable)

        WITH
            p,
            collect(DISTINCT s.name) AS spaces,
            collect(DISTINCT c.name) AS care_list,
            collect(DISTINCT b.name) AS budget_list,
            collect(DISTINCT t.name) AS time_list

        RETURN
            p.name AS name,
            p.description AS description,
            p.size AS size,
            p.activity_level AS activity_level,
            spaces,
            CASE
                WHEN size(care_list) > 0
                THEN care_list[0]
                ELSE null
            END AS care,
            CASE
                WHEN size(budget_list) > 0
                THEN budget_list[0]
                ELSE null
            END AS budget,
            CASE
                WHEN size(time_list) > 0
                THEN time_list[0]
                ELSE null
            END AS time

        ORDER BY name
        """
    )


# =========================================================
# SEARCH PETS
# =========================================================

def search_pets(keyword: str = ""):
    """
    ค้นหาสัตว์เลี้ยงจากชื่อหรือคำอธิบาย
    """

    keyword = keyword.strip()

    return query(
        """
        MATCH (p:Pet)

        WHERE
            $keyword = ""
            OR toLower(p.name) CONTAINS toLower($keyword)
            OR toLower(p.description) CONTAINS toLower($keyword)

        RETURN
            p.name AS name,
            p.description AS description,
            p.size AS size,
            p.activity_level AS activity_level

        ORDER BY name
        """,
        {
            "keyword": keyword
        },
    )


# =========================================================
# PET RECOMMENDATION
# =========================================================

def recommend_pets(
    space: str,
    budget: str,
    time: str,
):
    """
    ระบบแนะนำสัตว์เลี้ยง

    คะแนนเต็ม 3 คะแนน

    1 คะแนน = พื้นที่ตรง
    1 คะแนน = งบประมาณตรง
    1 คะแนน = เวลาตรง
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
            collect(DISTINCT b.name) AS budget_list,
            collect(DISTINCT t.name) AS time_list

        WITH
            p,
            spaces,
            CASE
                WHEN size(budget_list) > 0
                THEN budget_list[0]
                ELSE null
            END AS pet_budget,
            CASE
                WHEN size(time_list) > 0
                THEN time_list[0]
                ELSE null
            END AS pet_time

        WITH
            p,
            spaces,
            pet_budget,
            pet_time,

            CASE
                WHEN $space IN spaces
                THEN 1
                ELSE 0
            END

            +

            CASE
                WHEN pet_budget = $budget
                THEN 1
                ELSE 0
            END

            +

            CASE
                WHEN pet_time = $time
                THEN 1
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


# =========================================================
# GRAPH RELATIONSHIPS
# =========================================================

def get_pet_relationships():
    """
    ดึงความสัมพันธ์ของ Pet ทั้งหมด
    """

    return query(
        """
        MATCH (p:Pet)-[r]->(n)

        RETURN
            elementId(p) AS source_id,
            p.name AS source_name,
            labels(p)[0] AS source_label,

            type(r) AS relationship,

            elementId(n) AS target_id,
            coalesce(n.name, "Unknown") AS target_name,
            labels(n)[0] AS target_label

        ORDER BY
            source_name,
            relationship,
            target_name
        """
    )


# =========================================================
# DASHBOARD METRICS
# =========================================================

def get_dashboard_metrics():
    """
    ดึงข้อมูลสำหรับ Dashboard
    """

    pet_result = query(
        """
        MATCH (p:Pet)

        RETURN count(p) AS count
        """
    )

    space_result = query(
        """
        MATCH (s:LivingSpace)

        RETURN count(s) AS count
        """
    )

    relationship_result = query(
        """
        MATCH ()-[r]->()

        RETURN count(r) AS count
        """
    )

    return {
        "pets": (
            pet_result[0]["count"]
            if pet_result
            else 0
        ),
        "spaces": (
            space_result[0]["count"]
            if space_result
            else 0
        ),
        "relationships": (
            relationship_result[0]["count"]
            if relationship_result
            else 0
        ),
    }


# =========================================================
# CLOSE DRIVER
# =========================================================

def close_driver():
    """
    ปิด Neo4j Driver
    """

    try:
        get_driver().close()
    except Exception:
        pass