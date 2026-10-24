# -*- coding: utf-8 -*-
"""lab-agent 演示数据填充脚本（用户 / 实验室 / 设备）。

幂等：按用户名、实验室名、设备（实验室 + 名称）去重，可重复执行。
用法： .venv/Scripts/python.exe seed_demo_data.py
"""

import re
from datetime import datetime
from pathlib import Path

import bcrypt
import pymysql

BASE_DIR = Path(__file__).resolve().parent

# 用户管理页面可见用户数（不含 admin）
TARGET_USER_COUNT = 20
TARGET_LAB_COUNT = 10
DEFAULT_PASSWORD = "111111"


def read_database_config():
    text = (BASE_DIR / ".env").read_text(encoding="utf-8")
    url = re.search(r"^DATABASE_URL=(.+)$", text, re.M).group(1).strip()
    matched = re.match(
        r"mysql\+aiomysql://([^:]+):([^@]+)@([^:/]+):(\d+)/(\w+)", url
    )
    if not matched:
        raise SystemExit("无法解析 DATABASE_URL: %s" % url)

    user, password, host, port, database = matched.groups()
    return {
        "host": host,
        "port": int(port),
        "user": user,
        "password": password,
        "database": database,
        "charset": "utf8mb4",
    }


def hash_password(raw):
    return bcrypt.hashpw(raw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


# (username, nickname, phone, email)
NEW_USERS = [
    ("lisi", "李思远", "15784236150", "lisi@stu.edu.cn"),
    ("wangfang", "王芳", "13526741809", "wangfang@stu.edu.cn"),
    ("chenhao", "陈浩", "18874362051", "chenhao@stu.edu.cn"),
    ("liuyang", "刘洋", "15263874910", "liuyang@stu.edu.cn"),
    ("zhaomin", "赵敏", "17683920471", "zhaomin@stu.edu.cn"),
    ("sunqi", "孙琪", "13476290358", "sunqi@stu.edu.cn"),
    ("zhoujie", "周杰", "18562937401", "zhoujie@stu.edu.cn"),
    ("wuhao", "吴昊", "13905736284", "wuhao@stu.edu.cn"),
    ("zhengshuang", "郑爽", "15148730926", "zhengshuang@stu.edu.cn"),
    ("fenglin", "冯林", "18209463715", "fenglin@stu.edu.cn"),
    ("xujing", "徐静", "13671842905", "xujing@stu.edu.cn"),
    ("hewei", "何伟", "18930274816", "hewei@stu.edu.cn"),
    ("gaoyuan", "高远", "15362974018", "gaoyuan@stu.edu.cn"),
    ("linna", "林娜", "17748290536", "linna@stu.edu.cn"),
    ("luochen", "罗晨", "13284910576", "luochen@stu.edu.cn"),
    ("songyu", "宋雨", "18672039458", "songyu@stu.edu.cn"),
    ("tangkai", "唐凯", "15583947201", "tangkai@stu.edu.cn"),
    ("yinxi", "尹曦", "17824936570", "yinxi@stu.edu.cn"),
]

# name, description, location, capacity, open_time, close_time, status
NEW_LABS = [
    (
        "数计院二号机房",
        "面向全院公共课教学，配备 40 台中端台式机与多媒体教学系统，可预约用于上机实验与课程实训。",
        "信工楼A102",
        40,
        "08:00",
        "22:00",
        1,
    ),
    (
        "数计院三号机房",
        "学院规模最大的公共机房，45 台高性能台式机，支持程序设计、数据结构等课程的大班教学。",
        "信工楼A103",
        45,
        "08:00",
        "22:00",
        1,
    ),
    (
        "人工智能实验室",
        "配备多卡 GPU 服务器与深度学习工作站，面向机器学习、计算机视觉方向的科研训练与学科竞赛。",
        "信工楼B201",
        30,
        "08:30",
        "21:30",
        1,
    ),
    (
        "大数据技术实验室",
        "提供分布式计算集群与全闪存储阵列，支持 Hadoop、Spark 等大数据课程实验与课题研究。",
        "信工楼B202",
        30,
        "08:30",
        "21:30",
        1,
    ),
    (
        "软件工程实训室",
        "面向软件工程专业实训，支持需求分析、编码、测试全流程教学与项目团队协作开发。",
        "信工楼B301",
        36,
        "08:00",
        "22:00",
        1,
    ),
    (
        "网络空间安全实验室",
        "提供攻防靶场与安全实验一体机，支持渗透测试、防火墙策略配置等网络安全实验教学。",
        "信工楼C401",
        24,
        "09:00",
        "21:00",
        1,
    ),
    (
        "物联网创新实验室",
        "提供嵌入式开发板、传感器与示波器，面向物联网、智能硬件的课程实验与创新项目。",
        "信工楼C402",
        20,
        "08:30",
        "20:30",
        1,
    ),
    (
        "图形图像处理实验室",
        "配备专业图形工作站与数位屏，支持计算机图形学、数字媒体与三维建模相关课程。",
        "信工楼C403",
        28,
        "08:30",
        "21:30",
        1,
    ),
    (
        "智能机器人实验室",
        "提供六轴机械臂、移动机器人平台与 3D 打印设备，面向机器人控制与人工智能融合研究。",
        "信工楼D101",
        16,
        "09:00",
        "20:00",
        1,
    ),
]

# 实验室名称 -> [(设备名称, 型号规格, 数量, 状态, 说明)]
NEW_EQUIPMENT = {
    "数计院一号机房": [
        ("教学投影仪", "爱普生 CB-X06", 1, 1, "教学投影，支持 HDMI 与无线投屏"),
        ("教师机", "联想 ThinkCentre M760", 1, 1, "教师授课专用主机"),
        ("接入交换机", "H3C S5130-28S", 2, 1, "机房内千兆网络接入"),
    ],
    "数计院二号机房": [
        ("台式计算机", "惠普 ProDesk 480 G7", 40, 1, "学生上机用台式机"),
        ("教师机", "惠普 ProDesk 480 G7", 1, 1, "教师授课专用主机"),
        ("教学投影仪", "松下 PT-X3272", 1, 1, "教学投影"),
    ],
    "数计院三号机房": [
        ("台式计算机", "戴尔 OptiPlex 3000", 45, 1, "学生上机用台式机"),
        ("教师机", "戴尔 OptiPlex 3000", 1, 1, "教师授课专用主机"),
        ("立式空调", "格力 KFR-72LW", 2, 1, "机房环境控温"),
    ],
    "人工智能实验室": [
        ("GPU 服务器", "浪潮 NF5468M6 · A100 80G x4", 2, 1, "深度学习模型训练"),
        ("深度学习工作站", "i9-13900K · RTX 4090 · 128G", 4, 1, "模型调试与推理"),
        ("边缘计算开发套件", "NVIDIA Jetson Orin Nano", 6, 1, "边缘端模型部署实验"),
        ("4K 显示器", "戴尔 U2723QE 27 英寸", 8, 1, "实验工位显示器"),
    ],
    "大数据技术实验室": [
        ("集群服务器", "浪潮 NF5280M6 · 2xXeon 6338", 3, 1, "搭建分布式计算集群"),
        ("图形工作站", "Xeon W5-2455X · RTX A4000 · 256G", 6, 1, "大数据分析编程工作站"),
        ("全闪存储阵列", "华为 OceanStor 5310", 1, 1, "实验数据集中存储"),
        ("教学投影仪", "明基 MH760", 2, 1, "教学演示投影"),
    ],
    "软件工程实训室": [
        ("台式计算机", "联想 ThinkCentre M760", 36, 1, "实训开发用台式机"),
        ("教师机", "联想 ThinkCentre M760", 1, 1, "教师授课专用主机"),
        ("教学投影仪", "爱普生 CB-2247U", 1, 1, "教学投影"),
        ("激光打印机", "惠普 LaserJet M405dn", 2, 1, "实训文档打印"),
    ],
    "网络空间安全实验室": [
        ("安全实验一体机", "深信服 SFS-2000", 6, 1, "渗透测试与安全实验平台"),
        ("下一代防火墙", "华为 USG6610E", 2, 1, "防火墙策略配置实验"),
        ("靶场服务器", "浪潮 NF5180M6", 2, 1, "网络攻防靶场环境"),
        ("交换机", "思科 C9200L-24T", 4, 1, "实验网络组网"),
    ],
    "物联网创新实验室": [
        ("嵌入式开发板", "STM32F407 探索者", 20, 1, "嵌入式系统课程实验"),
        ("传感器实验套件", "温湿度 / 光照 / NFC 组合套件", 20, 1, "物联网感知层实验"),
        ("数字示波器", "泰克 TBS1102B", 6, 1, "电信号测量"),
        ("恒温焊台", "白光 936", 4, 1, "电路焊接与调试"),
    ],
    "图形图像处理实验室": [
        ("图形工作站", "i7-13700K · RTX A4000", 8, 1, "三维建模与渲染"),
        ("4K 显示器", "戴尔 U3223QE 32 英寸", 16, 1, "图形图像处理工位"),
        ("数位屏", "Wacom Cintiq 16", 8, 1, "数字绘图与平面设计"),
        ("三维扫描仪", "先临 EinScan SP", 2, 0, "设备维修中，暂停预约"),
    ],
    "智能机器人实验室": [
        ("六轴协作机械臂", "越疆 Dobot MG400", 4, 1, "机械臂控制与示教编程"),
        ("移动机器人平台", "图迈尔 TurtleBot 4", 6, 1, "SLAM 与自主导航实验"),
        ("3D 打印机", "拓竹 X1 Carbon", 3, 1, "结构件快速成型"),
        ("二维激光雷达", "思岚 A2M7", 6, 0, "维修中，待厂商更换"),
    ],
}


def main():
    now = datetime.now()
    config = read_database_config()
    conn = pymysql.connect(**config, autocommit=False, cursorclass=pymysql.cursors.DictCursor)

    try:
        with conn.cursor() as cursor:
            # ---------- 用户 ----------
            cursor.execute("select username from users")
            exists_users = {row["username"] for row in cursor.fetchall()}
            cursor.execute("select count(*) as c from users where role <> 'admin'")
            student_count = cursor.fetchone()["c"]

            added_users = 0
            for username, nickname, phone, email in NEW_USERS:
                if student_count >= TARGET_USER_COUNT:
                    break
                if username in exists_users:
                    continue
                cursor.execute(
                    "insert into users (username, password, nickname, role, email, phone, avatar, status,"
                    " create_time, update_time) values (%s, %s, %s, 'student', %s, %s, '', 1, %s, %s)",
                    (username, hash_password(DEFAULT_PASSWORD), nickname, email, phone, now, now),
                )
                added_users += 1
                student_count += 1

            # ---------- 实验室 ----------
            cursor.execute("select id, name from labs")
            lab_rows = cursor.fetchall()
            exist_labs = {row["name"]: row["id"] for row in lab_rows}

            added_labs = 0
            for name, description, location, capacity, open_time, close_time, status in NEW_LABS:
                if len(exist_labs) >= TARGET_LAB_COUNT:
                    break
                if name in exist_labs:
                    continue
                cursor.execute(
                    "insert into labs (name, description, img, location, capacity, open_time, close_time,"
                    " status, create_time, update_time) values (%s, %s, '', %s, %s, %s, %s, %s, %s, %s)",
                    (name, description, location, capacity, open_time, close_time, status, now, now),
                )
                exist_labs[name] = cursor.lastrowid
                added_labs += 1

            # ---------- 设备 ----------
            cursor.execute("select lab_id, name from equipment")
            exist_equipment = {(row["lab_id"], row["name"]) for row in cursor.fetchall()}

            added_equipment = 0
            for lab_name, items in NEW_EQUIPMENT.items():
                lab_id = exist_labs.get(lab_name)
                if not lab_id:
                    continue
                for name, spec, quantity, status, description in items:
                    if (lab_id, name) in exist_equipment:
                        continue
                    cursor.execute(
                        "insert into equipment (lab_id, name, description, img, spec, quantity, status,"
                        " create_time, update_time) values (%s, %s, %s, '', %s, %s, %s, %s, %s)",
                        (lab_id, name, description, spec, quantity, status, now, now),
                    )
                    exist_equipment.add((lab_id, name))
                    added_equipment += 1

        conn.commit()

        with conn.cursor() as cursor:
            cursor.execute("select count(*) as c from users")
            total_users = cursor.fetchone()["c"]
            cursor.execute("select count(*) as c from users where role <> 'admin'")
            total_students = cursor.fetchone()["c"]
            cursor.execute("select count(*) as c from labs")
            total_labs = cursor.fetchone()["c"]
            cursor.execute("select count(*) as c from equipment")
            total_equipment = cursor.fetchone()["c"]
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print("新增：用户 %d 个，实验室 %d 间，设备 %d 项" % (added_users, added_labs, added_equipment))
    print("当前总量：用户 %d（其中非管理员 %d），实验室 %d，设备 %d"
          % (total_users, total_students, total_labs, total_equipment))


if __name__ == "__main__":
    main()