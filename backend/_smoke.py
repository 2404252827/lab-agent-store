# -*- coding: utf-8 -*-
"""预约接口冒烟测试（结束后清理自造的测试数据）"""
import asyncio
import json
import urllib.error
import urllib.request
from datetime import date, timedelta

from sqlalchemy import text

from app.database import async_engine
from app.utils.jwt import create_access_token

BASE = "http://127.0.0.1:8000"
ADMIN = create_access_token(1)
STU_A = create_access_token(9)
STU_B = create_access_token(10)

LAB_ID = 12
LAB_ID_MACHINE = 4
tomorrow = (date.today() + timedelta(days=1)).isoformat()
yesterday = (date.today() - timedelta(days=1)).isoformat()

passed, failed = [], []


def call(method, path, token=None, body=None):
    req = urllib.request.Request(BASE + path, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    data = json.dumps(body).encode("utf-8") if body is not None else None
    try:
        with urllib.request.urlopen(req, data) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return {"code": exc.code, "message": exc.read().decode("utf-8"), "data": None}


def check(name, cond, extra=""):
    (passed if cond else failed).append(name)
    print(("  OK   " if cond else "  FAIL ") + name + ((" -> " + str(extra)) if extra else ""))


def reserve(token, lab_id, d, start, end, remark=""):
    return call("POST", "/api/reservation", token,
                {"lab_id": lab_id, "date": d, "start_time": start, "end_time": end, "remark": remark})


# 上一轮跑残留的数据先清掉，保证从干净状态开始
async def sql_run(stmt, args=None):
    async with async_engine.begin() as conn:
        await conn.execute(text(stmt), args or {})


async def sql_rows(stmt, args=None):
    async with async_engine.connect() as conn:
        return (await conn.execute(text(stmt), args or {})).fetchall()


async def prepare():
    await sql_run("delete from reservations")


async def main():
    await prepare()

    print("1) 预约与日期接口：")
    r = reserve(STU_A, LAB_ID, tomorrow, "10:00", "12:00", "组会讨论")
    check("学生A预约成功", r.get("code") == 200, r.get("message"))

    r = call("GET", f"/api/reservation/dates?lab_id={LAB_ID}", STU_B)
    check("dates 返回该日期", r.get("code") == 200 and r.get("data") == [tomorrow], r)

    r = call("GET", "/api/reservation/dates?lab_id=999", STU_B)
    check("无预约实验室返回空数组", r.get("code") == 200 and r.get("data") == [], r)

    print("2) 业务校验：")
    r = reserve(STU_A, LAB_ID, tomorrow, "14:00", "15:00")
    check("同一人同天重复预约被拒", "重复预约" in str(r.get("message")), r.get("message"))
    r = reserve(STU_B, LAB_ID, tomorrow, "11:00", "13:00")
    check("他人时段重叠被拒", "已经被预约" in str(r.get("message")), r.get("message"))
    r = reserve(STU_B, LAB_ID, tomorrow, "15:00", "16:00")
    check("他人不重叠时段可预约", r.get("code") == 200, r.get("message"))
    r = reserve(STU_B, LAB_ID, yesterday, "10:00", "11:00")
    check("昨天预约被拒", "提前一天" in str(r.get("message")), r.get("message"))
    r = reserve(STU_B, LAB_ID, date.today().isoformat(), "10:00", "11:00")
    check("今天预约被拒", "提前一天" in str(r.get("message")), r.get("message"))
    r = reserve(STU_B, LAB_ID, tomorrow, "10:00", "10:00")
    check("起止时间相等被拒", "晚于开始时间" in str(r.get("message")), r.get("message"))
    r = reserve(STU_B, LAB_ID, tomorrow, "18:00", "21:00")
    check("超出开放时间被拒", "开放时间" in str(r.get("message")), r.get("message"))
    r = reserve(STU_B, 99999, tomorrow, "10:00", "11:00")
    check("实验室不存在被拒", "实验室不存在" in str(r.get("message")), r.get("message"))
    r = reserve(STU_B, LAB_ID, "2026-13-45", "10:00", "11:00")
    check("非法日期被拒(422)", r.get("code") == 422, r.get("message"))

    print("3) 列表与筛选（当前共 2 条：学生A 1 条 + 学生B 1 条）：")
    r = call("GET", "/api/reservation/list?page=1&page_size=10", STU_A)
    check("学生只看到自己的预约", r["code"] == 200 and r["data"]["total"] == 1
          and all(x["user_id"] == 9 for x in r["data"]["list"]), r["data"]["total"])
    r = call("GET", "/api/reservation/list?page=1&page_size=10", ADMIN)
    check("管理员看到全部预约", r["code"] == 200 and r["data"]["total"] == 2, r["data"]["total"])
    check("列表带 username/nickname/lab_name",
          all(x.get("lab_name") and x.get("username") and x.get("nickname") for x in r["data"]["list"]),
          r["data"]["list"][0] if r["data"]["list"] else None)
    r = call("GET", "/api/reservation/list?page=1&page_size=10&status=0", ADMIN)
    check("status=0 筛选生效", r["data"]["total"] == 2, r["data"]["total"])
    r = call("GET", "/api/reservation/list?page=1&page_size=10&status=1", ADMIN)
    check("status=1 无数据", r["data"]["total"] == 0, r["data"]["total"])
    r = call("GET", f"/api/reservation/list?page=1&page_size=10&lab_id={LAB_ID_MACHINE}", ADMIN)
    check("lab_id 筛选生效", r["data"]["total"] == 0, r["data"]["total"])
    r = call("GET", f"/api/reservation/list?page=1&page_size=10&lab_id={LAB_ID}", ADMIN)
    check("lab_id 命中", r["data"]["total"] == 2, r["data"]["total"])

    print("4) 审核与取消：")
    rid_a = call("GET", "/api/reservation/list", STU_A)["data"]["list"][0]["id"]
    rid_b = call("GET", "/api/reservation/list", STU_B)["data"]["list"][0]["id"]
    r = call("PUT", f"/api/reservation/{rid_a}/audit", ADMIN, {"status": 1})
    check("管理员同意", r.get("code") == 200, r.get("message"))
    r = call("PUT", f"/api/reservation/{rid_a}/audit", ADMIN, {"status": 2})
    check("已审核不能再审", "不支持审核" in str(r.get("message")), r.get("message"))
    r = call("PUT", f"/api/reservation/{rid_b}/audit", STU_B, {"status": 1})
    check("学生无审核权限", "管理员" in str(r.get("message")), r.get("message"))
    r = call("PUT", f"/api/reservation/{rid_a}/cancel", STU_B)
    check("非本人不能取消", "无权限" in str(r.get("message")), r.get("message"))
    r = call("PUT", f"/api/reservation/{rid_a}/cancel", STU_A)
    check("已同意的预约不能取消", "不能取消" in str(r.get("message")), r.get("message"))
    r = call("GET", f"/api/reservation/dates?lab_id={LAB_ID}", STU_B)
    check("已同意仍标红", r.get("data") == [tomorrow], r.get("data"))
    r = call("PUT", f"/api/reservation/{rid_b}/cancel", STU_B)
    check("本人取消待审核预约", r.get("code") == 200, r.get("message"))
    r = call("GET", f"/api/reservation/dates?lab_id={LAB_ID}", STU_B)
    check("取消后另一条仍标红", r.get("data") == [tomorrow], r.get("data"))
    r = call("GET", "/api/reservation/list?page=1&page_size=10&status=3", ADMIN)
    check("取消后状态为 3", r["data"]["total"] == 1, r["data"]["total"])

    print("5) 关闭实验室 & 删除实验室：")
    await sql_run("update labs set status = 0 where id = :i", {"i": LAB_ID})
    try:
        r = reserve(STU_A, LAB_ID, (date.today() + timedelta(days=3)).isoformat(), "10:00", "11:00")
        check("关闭的实验室不能预约", "已关闭" in str(r.get("message")), r.get("message"))
    finally:
        await sql_run("update labs set status = 1 where id = :i", {"i": LAB_ID})

    r = call("POST", "/api/lab", ADMIN, {"name": "预约测试实验室", "location": "信工楼Z999",
                                         "capacity": 5, "open_time": "08:00", "close_time": "22:00"})
    lab_test_id = r["data"]["id"]
    reserve(STU_A, lab_test_id, (date.today() + timedelta(days=2)).isoformat(), "10:00", "11:00")
    r = call("DELETE", f"/api/lab/{lab_test_id}", ADMIN)
    check("有预约记录的实验室禁止删除", "预约记录" in str(r.get("message")), r.get("message"))
    await sql_run("delete from reservations where lab_id = :i", {"i": lab_test_id})
    r = call("DELETE", f"/api/lab/{lab_test_id}", ADMIN)
    check("清理后实验室可删除", r.get("code") == 200, r.get("message"))

    rows = await sql_rows("select id, lab_id, user_id, date, start_time, end_time, status from reservations order by id")
    print("\n清理前的 reservations：")
    for row in rows:
        print("   ", list(row))
    await sql_run("delete from reservations")
    print("清理后行数:", (await sql_rows("select count(*) from reservations"))[0][0])
    await async_engine.dispose()


asyncio.run(main())

print("\n通过 %d 项，失败 %d 项" % (len(passed), len(failed)))
if failed:
    print("失败项：", failed)