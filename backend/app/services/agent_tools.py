from datetime import datetime
import logging

from pydantic import ValidationError
from app.common.exceptions import BusinessException
from app.database import AsyncSessionFactory
from app.models.user import User
from langchain_core.tools import tool
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.reservation import ReservationCreateRequest
from app.services import (
    equipment_service,
    lab_service,
    rag_service,
    reservation_service,
)

logger = logging.getLogger(__name__)
# 单次查询最多返回多少条，避免把上下文撑爆
MAX_ROWS = 20
STATUS_TEXT = {0: "待审核", 1: "已同意", 2: "已驳回", 3: "已取消"}
STATUS_VALUE = {"待审核": 0, "已同意": 1, "已驳回": 2, "已取消": 3}


def _parse_status(status: str) -> tuple[int | None, str | None]:
    """把用户说的状态词转成状态码，返回 (状态码, 错误提示)"""

    status = (status or "").strip()

    if not status:
        return None, None

    if status in STATUS_VALUE:
        return STATUS_VALUE[status], None

    return (
        None,
        f"无法识别的预约状态「{status}」，可选：待审核、已同意、已驳回、已取消。",
    )


async def _resolve_lab(db: AsyncSession, lab_name: str):
    page = await lab_service.get_lab_page_list(db, 1, 10, lab_name)
    labs = list(page.list or [])

    for lab in labs:
        if lab.name == lab_name:
            return lab, []

    return None, labs


# 工具返回字符串就行，agent会把返回值封装成AIMessage
def build_tools(user: User):
    """为当前请求造一批工具

    Args:
        user: 当前登录用户

    Returns:
        可以直接交给 LangGraph ToolNode 的工具列表
    """

    @tool
    async def get_current_date():
        """获取今天的日期、星期和当前时间。

        只要涉及日期换算就必须先调用它。用户在对话里说「今天」「明天」「后天」
        「下周三」时，你要先调这个工具拿到今天几号，再换算成具体日期。
        绝对不要凭记忆猜日期。

        Returns:
            形如「今天是 2026-10-16（星期五），当前时间 14:30」的文本。
        """

        now = datetime.now()
        weekday = "一二三四五六日"[now.weekday()]

        return (
            f"今天是 {now.strftime('%Y-%m-%d')}（星期{weekday}），"
            f"当前时间 {now.strftime('%H:%M')}。"
        )

    @tool
    async def query_labs(keyword: str = ""):
        """查询实验室列表信息。

        用户问「有哪些实验室」「XX 实验室在哪里」「能坐多少人」「开放时间」
        这类问题时用这个工具。返回名称、位置、容纳人数、开放时间、开关状态。

        Args:
            keyword: 实验室名称关键字，用于模糊筛选。不需要筛选时传空字符串。
        """

        keyword = keyword.strip() if keyword else ""
        try:
            async with AsyncSessionFactory() as db:
                page = await lab_service.get_lab_page_list(db, 1, MAX_ROWS, keyword)

                if not page.list:
                    if keyword:
                        return f"没有找到名称包含「{keyword}」的实验室。"
                    return "系统里目前还没有录入任何实验室。"

                lines = []
                for lab in page.list:
                    lines.append(
                        f"- {lab.name}｜位置：{lab.location or '未填写'}"
                        f"｜容纳：{lab.capacity} 人"
                        f"｜开放时间：{lab.open_time or '未设置'} ~ {lab.close_time or '未设置'}"
                        f"｜状态：{'开放中' if lab.status == 1 else '已关闭'}"
                    )

                return (
                    f"共 {page.total} 个实验室，最多列出 {MAX_ROWS} 个：\n"
                    + "\n".join(lines)
                )

        except BusinessException as exc:
            return f"查询实验室失败：{exc.message}"
        except Exception:
            logger.exception("query_labs 执行失败")
            return "查询实验室信息时出错了，请稍后重试。"

    @tool
    async def query_equipment(lab_name: str = "", keyword: str = ""):
        """查询实验设备信息。

        用户问「XX 实验室有哪些设备」「有没有示波器」「设备在哪个实验室」
        「设备是不是在维修」这类问题时用。返回名称、型号、数量、状态、所属实验室。

        Args:
            lab_name: 限定在某个实验室里查，填实验室名称。查全部时传空字符串。
            keyword: 设备名称关键字，用于模糊筛选。不需要筛选时传空字符串。
        """
        try:
            async with AsyncSessionFactory() as db:
                lab_id = None

                if lab_name.strip():
                    lab, candidates = await _resolve_lab(db, lab_name.strip())

                    if lab is None:
                        like = ",".join(candidates)
                        hint = (
                            f"类似的实验室有：{like}" if like else "也没有类似的实验室"
                        )
                        return f"没有找到叫{lab_name}的实验室。{hint}"

                    lab_id = lab.id

                page = await equipment_service.get_equipment_page_list(
                    db, 1, MAX_ROWS, keyword.strip(), lab_id
                )

                if not page.list:
                    scope = f"{lab_name}实验室里" if lab_name.strip() else "系统里"
                    extra = f"名称包含{keyword}的" if keyword.strip() else ""
                    return f"{scope}没有找到{extra}设备"

                lines = []
                for item in page.list:
                    lines.append(
                        f"- {item.name}｜所属实验室：{item.lab_name or '未知'}"
                        f"｜型号：{item.spec or '未填写'}"
                        f"｜数量：{item.quantity}"
                        f"｜状态：{'正常' if item.status == 1 else '维修中'}"
                        f"｜说明：{item.description or '无'}"
                    )

                return (
                    f"共 {page.total} 台设备，最多列出 {MAX_ROWS} 台：\n"
                    + "\n".join(lines)
                )
        except BusinessException as exc:
            return f"查询设备失败：{exc.message}"
        except Exception:
            logger.exception("query_equipment 执行失败")
            return "查询设备信息时出错了，请稍后重试。"

    @tool
    async def query_my_reservations(status: str = ""):
        """查询当前登录用户自己的实验室预约记录。

        用户问「我约了哪些」「我的预约通过了没」这类问题时用。
        只能查到当前用户自己的记录，查不到别人的。

        Args:
            status: 按状态筛选，可选：待审核 / 已同意 / 已驳回 / 已取消。
                    不筛选时传空字符串。
        """

        try:
            status_code, error = _parse_status(status)

            if error:
                return error

            async with AsyncSessionFactory() as db:
                page = await reservation_service.get_reservation_page_list(
                    db, user, 1, MAX_ROWS, status_code, None
                )

            if not page.list:
                scope = f"状态为「{status}」的" if status.strip() else ""
                return f"你目前没有{scope}预约记录。"

            lines = []
            for item in page.list:
                lines.append(
                    f"- {item.date} {item.start_time}~{item.end_time}"
                    f"｜{item.lab_name or '未知实验室'}"
                    f"｜状态：{STATUS_TEXT.get(item.status, item.status)}"
                    f"｜备注：{item.remark or '无'}"
                )

            return (
                f"共 {page.total} 条预约记录，最多列出 {MAX_ROWS} 条：\n"
                + "\n".join(lines)
            )

        except BusinessException as exc:
            return f"查询预约记录失败：{exc.message}"
        except Exception:
            logger.exception("query_my_reservations 执行失败")
            return "查询预约记录时出错了，请稍后重试。"

    @tool
    async def create_lab_reservation(
        lab_name: str,
        date: str,
        start_time: str,
        end_time: str,
        remark: str = "",
    ) -> str:
        """替当前登录用户提交一条实验室预约申请。

        用户明确要预约实验室时用。提交后状态是「待审核」，需要管理员审核才生效。

        调用前必须先跟用户确认好四项：实验室、日期、开始时间、结束时间。
        日期必须先用 get_current_date 查出今天几号，再根据用户说的
        「明天 / 后天 / 下周三」换算成具体日期，绝对不要自己编一个日期。

        Args:
            lab_name: 实验室名称，例如「人工智能实验室」。
            date: 预约日期，格式必须是 YYYY-MM-DD，例如 2026-10-20。
                  必须比今天至少晚一天，当天和过去的日期都不允许。
            start_time: 开始时间，格式 HH:MM（24 小时制补零），例如 09:00。
            end_time: 结束时间，格式 HH:MM，必须晚于开始时间。
            remark: 备注，可选，用来写实验内容。
        """

        try:
            async with AsyncSessionFactory() as db:
                lab, candidates = await _resolve_lab(db, lab_name.strip())

                if lab is None:
                    names = "、".join(item.name for item in candidates)
                    hint = f"名称相近的有：{names}。" if names else ""
                    return (
                        f"没有找到叫「{lab_name}」的实验室。{hint}"
                        "请跟用户确认准确的实验室名称再提交。"
                    )

                if lab.status != 1:
                    return f"「{lab.name}」当前已关闭，暂不可预约。"

                try:
                    payload = ReservationCreateRequest(
                        lab_id=lab.id,
                        date=date.strip(),
                        start_time=start_time.strip(),
                        end_time=end_time.strip(),
                        remark=remark.strip() or None,
                        status=0,
                    )
                except ValidationError as exc:
                    detail = str(exc.errors()[0].get("msg", "格式不正确"))
                    detail = detail.replace("Value error, ", "")
                    return (
                        f"参数格式不对（{detail}）。日期要 YYYY-MM-DD，"
                        "时间要 HH:MM（24 小时制补零），请修正后重试。"
                    )

                result = await reservation_service.create_reservation(payload, user, db)

        except BusinessException as exc:
            return f"提交预约失败：{exc.message}"
        except Exception:
            logger.exception("create_lab_reservation 执行失败")
            return "提交预约时出错了，请稍后重试。"

        return (
            "预约已提交，等待管理员审核：\n"
            f"- 实验室：{lab.name}（{lab.location or '位置未填写'}）\n"
            f"- 时间：{result.date} {result.start_time} ~ {result.end_time}\n"
            "- 状态：待审核\n"
            f"- 备注：{result.remark or '无'}"
        )

    @tool
    async def search_lab_rules(question: str) -> str:
        """在实验室管理系统的知识库文档里检索规章制度。

        用户问「规则 / 流程 / 为什么 / 能不能」这类需要查制度的问题时用，
        比如「为什么不能预约今天」「取消预约有什么限制」「删除实验室要什么条件」。

        Args:
            question: 要检索的问题原话，尽量保留用户措辞，不要改写成关键词。
        """

        try:
            hits = await rag_service.retrieve(question)

            if not hits:
                return (
                    "知识库里没有检索到相关规则。请如实告诉用户查不到，不要凭空推测。"
                )

            parts = [f"[来源：{hit['source']}]\n{hit['document']}" for hit in hits]

            return "以下是从系统知识库检索到的资料：\n\n" + "\n\n".join(parts)

        except BusinessException as exc:
            return f"检索知识库失败：{exc.message}"
        except Exception:
            logger.exception("search_lab_rules 执行失败")
            return "检索知识库时出错了，请稍后重试。"

    return [
        get_current_date,
        query_labs,
        query_equipment,
        query_my_reservations,
        create_lab_reservation,
        search_lab_rules,
    ]
