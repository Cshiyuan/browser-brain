"""
Streamlit Web界面 - AI智能旅行规划助手
"""
import streamlit as st
import asyncio
import sys
import json
import os
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents.planner_agent import PlannerAgent
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# 数据存储目录
DATA_DIR = Path(__file__).parent.parent / "data"
PLANS_DIR = DATA_DIR / "plans"
PLANS_DIR.mkdir(parents=True, exist_ok=True)

# 页面配置
st.set_page_config(
    page_title="AI智能旅行规划助手",
    page_icon="🌏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 3rem;
    }
    .result-box {
        background-color: #f0f8ff;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #1E88E5;
    }
    .stButton>button {
        width: 100%;
        background-color: #1E88E5;
        color: white;
        font-size: 1.2rem;
        padding: 0.75rem;
        border-radius: 10px;
    }
    .log-box {
        background-color: #f5f5f5;
        padding: 15px;
        border-radius: 5px;
        font-family: monospace;
        font-size: 0.9rem;
        max-height: 400px;
        overflow-y: auto;
    }
    .attraction-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# 页面标题
st.markdown('<div class="main-header">🌏 AI智能旅行规划助手</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">输入目的地，AI自动搜索景点、酒店、机票，生成个性化旅行方案</div>', unsafe_allow_html=True)

# 初始化session state
if 'planning_logs' not in st.session_state:
    st.session_state.planning_logs = []
if 'current_plan' not in st.session_state:
    st.session_state.current_plan = None
if 'attraction_details' not in st.session_state:
    st.session_state.attraction_details = {}
if 'is_planning' not in st.session_state:
    st.session_state.is_planning = False

# 侧边栏 - 配置选项
with st.sidebar:
    st.header("⚙️ 配置选项")

    headless_mode = st.checkbox("无头模式（隐藏浏览器）", value=False)  # 默认显示浏览器,更像真实用户
    max_notes = st.slider("每个景点最大笔记数", min_value=3, max_value=20, value=10)

    st.divider()

    # 日志级别过滤
    st.header("📊 日志过滤")
    log_levels = st.multiselect(
        "显示的日志级别",
        ["DEBUG", "INFO", "WARNING", "ERROR"],
        default=["INFO", "WARNING", "ERROR"],
        help="选择要显示的日志级别"
    )

    st.divider()

    st.header("📊 功能状态")
    st.success("✅ 小红书信息收集")
    st.success("✅ 官网信息提取")
    st.warning("⏳ 携程酒店查询（待开发）")
    st.warning("⏳ 携程机票查询（待开发）")

    st.divider()

    # 历史方案
    st.header("📚 历史方案")
    plan_files = sorted(PLANS_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
    if plan_files:
        selected_plan = st.selectbox(
            "选择历史方案",
            options=[""] + [f.stem for f in plan_files],
            format_func=lambda x: "请选择" if x == "" else x
        )

        if selected_plan and st.button("📖 加载历史方案"):
            plan_path = PLANS_DIR / f"{selected_plan}.json"
            try:
                with open(plan_path, 'r', encoding='utf-8') as f:
                    plan_data = json.load(f)
                st.session_state.current_plan = plan_data
                st.success("✅ 历史方案已加载")
                st.rerun()
            except Exception as e:
                st.error(f"❌ 加载失败: {e}")
    else:
        st.info("暂无历史方案")

    st.divider()

    st.header("ℹ️ 关于")
    st.info("""
    本系统基于AI和浏览器自动化技术：
    - 从小红书深度搜索景点信息
    - 智能提取官方网站链接
    - 自动生成旅行方案

    **技术栈**：
    - Browser-Use (AI自动化)
    - Playwright (浏览器自动化)
    - Streamlit (前端界面)
    - Python AsyncIO (异步并发)
    """)

# 主界面 - 输入表单
st.header("📝 请输入旅行计划")

col1, col2 = st.columns(2)

with col1:
    departure = st.text_input(
        "📍 出发地",
        placeholder="例如：深圳",
        help="请输入你的出发城市"
    )

    destination = st.text_input(
        "📍 目的地",
        placeholder="例如：北京",
        help="请输入你想去的城市"
    )

with col2:
    start_date = st.date_input(
        "📅 开始日期",
        value=datetime.now().date(),
        help="请选择出发日期"
    )

    end_date = st.date_input(
        "📅 结束日期",
        value=(datetime.now() + timedelta(days=6)).date(),
        help="请选择返程日期"
    )

    # 自动计算天数
    if start_date and end_date:
        days = (end_date - start_date).days + 1
        if days <= 0:
            st.error("⚠️ 结束日期必须晚于开始日期")
            days = 1
        else:
            st.info(f"🗓️ 总共 **{days}** 天")
    else:
        days = 7

must_visit = st.text_input(
    "🎯 必去景点",
    placeholder="例如：故宫,天安门,颐和园,长城",
    help="请输入必去景点，用逗号分隔"
)

# 添加更多选项（可折叠）
with st.expander("🔧 高级选项"):
    col3, col4 = st.columns(2)

    with col3:
        budget_type = st.selectbox(
            "💰 预算类型",
            ["不限", "经济型", "舒适型", "奢华型"],
            help="预算类型（当前版本仅供参考）"
        )

    with col4:
        travel_style = st.multiselect(
            "🎨 旅行风格",
            ["历史文化", "自然风光", "美食探店", "购物娱乐", "亲子游", "情侣游"],
            help="选择你的旅行偏好（当前版本仅供参考）"
        )

st.divider()

# 日志过滤函数
def filter_logs(logs, levels):
    """根据日志级别过滤日志"""
    if not levels:
        return logs
    filtered = []
    for log in logs:
        for level in levels:
            if level in log or (level == "INFO" and not any(l in log for l in ["DEBUG", "WARNING", "ERROR"])):
                filtered.append(log)
                break
    return filtered

# 日志颜色标记函数
def colorize_log(log):
    """为不同级别的日志添加颜色标记"""
    if "ERROR" in log or "❌" in log:
        return f"🔴 {log}"
    elif "WARNING" in log or "⚠️" in log:
        return f"🟡 {log}"
    elif "DEBUG" in log:
        return f"🔵 {log}"
    elif "✅" in log or "成功" in log:
        return f"🟢 {log}"
    else:
        return f"⚪ {log}"

# 开始规划按钮
if st.button("🚀 开始智能规划", type="primary"):
    # 验证输入
    if not departure or not destination:
        st.error("❌ 请填写完整信息：出发地和目的地不能为空")
    else:
        # 解析必去景点(可以为空)
        must_visit_list = [spot.strip() for spot in must_visit.split(",") if spot.strip()] if must_visit else []

        # 设置规划状态
        st.session_state.is_planning = True
        st.session_state.planning_logs = []

        # 创建实时日志显示区域
        log_expander = st.expander("🔍 实时日志", expanded=True)
        with log_expander:
            log_container = st.empty()

        # 显示规划进度
        with st.spinner("🔍 正在智能规划中，请稍候..."):
            # 创建进度指示器
            progress_bar = st.progress(0)
            status_text = st.empty()

            # 异步执行规划任务
            async def run_planning():
                # 更新进度
                st.session_state.planning_logs = []

                # 定义日志回调函数
                def add_log(message: str):
                    st.session_state.planning_logs.append(message)
                    # 实时更新日志显示
                    filtered = filter_logs(st.session_state.planning_logs, log_levels)
                    colored_logs = [colorize_log(log) for log in filtered[-50:]]  # 最新50条
                    log_container.text("\n".join(colored_logs))

                st.session_state.planning_logs.append("📦 初始化浏览器...")
                status_text.text("📦 初始化浏览器...")
                progress_bar.progress(10)

                planner = PlannerAgent(headless=headless_mode, log_callback=add_log)

                try:
                    st.session_state.planning_logs.append("🔍 开始收集景点信息...")
                    status_text.text("🔍 收集景点信息...")
                    progress_bar.progress(30)

                    result = await planner.plan_trip(
                        departure=departure,
                        destination=destination,
                        days=int(days),
                        must_visit=must_visit_list
                    )

                    st.session_state.planning_logs.append("✅ 规划完成！")
                    status_text.text("✅ 规划完成！")
                    progress_bar.progress(100)

                    # 保存方案
                    plan_data = {
                        "timestamp": datetime.now().isoformat(),
                        "departure": departure,
                        "destination": destination,
                        "days": days,
                        "must_visit": must_visit_list,
                        "plan_text": result,
                        "logs": st.session_state.planning_logs
                    }

                    # 保存到文件
                    plan_filename = f"{destination}_{days}日游_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    plan_path = PLANS_DIR / plan_filename
                    with open(plan_path, 'w', encoding='utf-8') as f:
                        json.dump(plan_data, f, ensure_ascii=False, indent=2)

                    st.session_state.current_plan = plan_data

                    return result, None

                except Exception as e:
                    logger.error(f"规划失败: {e}", exc_info=True)
                    st.session_state.planning_logs.append(f"❌ 错误: {e}")
                    return None, str(e)

            # 运行异步任务
            try:
                result, error = asyncio.run(run_planning())

                # 清除进度指示器
                progress_bar.empty()
                status_text.empty()

                # 规划完成，更新状态
                st.session_state.is_planning = False

                if error:
                    st.error(f"❌ 规划失败: {error}")
                    # 显示错误日志
                    if st.session_state.planning_logs:
                        with st.expander("📋 查看日志"):
                            st.markdown('<div class="log-box">', unsafe_allow_html=True)
                            for log in st.session_state.planning_logs:
                                st.text(log)
                            st.markdown('</div>', unsafe_allow_html=True)
                else:
                    # 显示结果
                    st.success("✅ 旅行方案生成成功！")

                    # 使用tabs展示不同部分
                    tab1, tab2, tab3, tab4 = st.tabs(["📋 完整方案", "🎯 景点详情", "📊 执行日志", "💡 实用贴士"])

                    with tab1:
                        st.markdown('<div class="result-box">', unsafe_allow_html=True)
                        st.markdown(result)
                        st.markdown('</div>', unsafe_allow_html=True)

                        # 下载按钮
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.download_button(
                                label="📥 下载方案 (TXT)",
                                data=result,
                                file_name=f"{destination}_{days}日游方案.txt",
                                mime="text/plain"
                            )
                        with col_b:
                            st.download_button(
                                label="📥 下载方案 (JSON)",
                                data=json.dumps(st.session_state.current_plan, ensure_ascii=False, indent=2),
                                file_name=f"{destination}_{days}日游方案.json",
                                mime="application/json"
                            )

                    with tab2:
                        st.subheader("🎯 景点详细信息")
                        # 这里可以展示每个景点的详细信息
                        if must_visit_list:
                            for idx, attraction in enumerate(must_visit_list, 1):
                                with st.container():
                                    st.markdown(f'<div class="attraction-card">', unsafe_allow_html=True)
                                    st.markdown(f"### {idx}. {attraction}")
                                    st.markdown(f"**城市**: {destination}")
                                    st.markdown("**数据来源**: AI智能收集")
                                    st.info("💡 详细信息将在后续版本中展示（包括门票、开放时间、推荐游玩时长等）")
                                    st.markdown('</div>', unsafe_allow_html=True)
                        else:
                            st.info("暂无景点详情")

                    with tab3:
                        st.subheader("📊 规划执行日志")

                        # 日志过滤和导出工具栏
                        col_log1, col_log2 = st.columns([3, 1])
                        with col_log1:
                            filter_levels = st.multiselect(
                                "过滤日志级别",
                                ["DEBUG", "INFO", "WARNING", "ERROR"],
                                default=log_levels,
                                key="log_filter_tab3"
                            )
                        with col_log2:
                            if st.session_state.planning_logs:
                                log_export_text = "\n".join(st.session_state.planning_logs)
                                st.download_button(
                                    label="📥 导出日志",
                                    data=log_export_text,
                                    file_name=f"planning_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                    mime="text/plain",
                                    key="download_log_tab3"
                                )

                        # 显示过滤后的日志
                        if st.session_state.planning_logs:
                            filtered_logs = filter_logs(st.session_state.planning_logs, filter_levels)
                            st.markdown('<div class="log-box">', unsafe_allow_html=True)
                            for log in filtered_logs:
                                colored_log = colorize_log(log)
                                st.text(colored_log)
                            st.markdown('</div>', unsafe_allow_html=True)
                            st.caption(f"共 {len(filtered_logs)} 条日志（过滤前: {len(st.session_state.planning_logs)} 条）")
                        else:
                            st.info("暂无日志")

                    with tab4:
                        st.subheader("💡 实用贴士")
                        st.markdown(f"""
                        ### 🗺️ {destination}旅行建议

                        #### 📅 行程时长
                        - 建议游玩时长: {days}天

                        #### 🎫 预订建议
                        - 提前预订景点门票，避免现场排队
                        - 关注景点官网或小红书获取最新优惠信息

                        #### 🚗 交通建议
                        - 出发地: {departure}
                        - 目的地: {destination}
                        - 建议查询高铁/飞机票价格对比

                        #### ⚠️ 注意事项
                        - 查看天气预报，准备合适衣物
                        - 景点可能有淡旺季价格差异
                        - 部分景点需要提前预约

                        #### 📱 实用APP推荐
                        - 小红书: 查看最新游记和攻略
                        - 高德/百度地图: 导航和路线规划
                        - 大众点评/美团: 餐饮和住宿预订
                        """)

            except Exception as e:
                st.error(f"❌ 系统错误: {e}")
                logger.error(f"系统错误: {e}", exc_info=True)

# 显示历史方案（如果已加载）
if st.session_state.current_plan and not st.button("🚀 开始智能规划", type="primary", key="btn_replan"):
    st.divider()
    st.success("📖 已加载历史方案")

    plan_data = st.session_state.current_plan

    # 显示方案信息
    st.markdown(f"""
    **出发地**: {plan_data.get('departure', 'N/A')}
    **目的地**: {plan_data.get('destination', 'N/A')}
    **游玩天数**: {plan_data.get('days', 'N/A')}天
    **生成时间**: {plan_data.get('timestamp', 'N/A')}
    """)

    # 使用tabs展示
    tab1, tab2, tab3, tab4 = st.tabs(["📋 完整方案", "🎯 景点详情", "📊 执行日志", "💡 实用贴士"])

    with tab1:
        st.markdown('<div class="result-box">', unsafe_allow_html=True)
        st.markdown(plan_data.get('plan_text', '暂无内容'))
        st.markdown('</div>', unsafe_allow_html=True)

        # 下载按钮
        col_a, col_b = st.columns(2)
        with col_a:
            st.download_button(
                label="📥 下载方案 (TXT)",
                data=plan_data.get('plan_text', ''),
                file_name=f"{plan_data.get('destination', 'plan')}_{plan_data.get('days', 'N')}日游方案.txt",
                mime="text/plain",
                key="download_txt_result"
            )
        with col_b:
            st.download_button(
                label="📥 下载方案 (JSON)",
                data=json.dumps(plan_data, ensure_ascii=False, indent=2),
                file_name=f"{plan_data.get('destination', 'plan')}_{plan_data.get('days', 'N')}日游方案.json",
                mime="application/json",
                key="download_json_result"
            )

    with tab2:
        st.subheader("🎯 景点详细信息")
        must_visit = plan_data.get('must_visit', [])
        if must_visit:
            for idx, attraction in enumerate(must_visit, 1):
                with st.container():
                    st.markdown(f'<div class="attraction-card">', unsafe_allow_html=True)
                    st.markdown(f"### {idx}. {attraction}")
                    st.markdown(f"**城市**: {plan_data.get('destination', 'N/A')}")
                    st.markdown("**数据来源**: AI智能收集")
                    st.info("💡 详细信息将在后续版本中展示（包括门票、开放时间、推荐游玩时长等）")
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("暂无景点详情")

    with tab3:
        st.subheader("📊 规划执行日志")
        logs = plan_data.get('logs', [])

        # 日志过滤和导出工具栏
        col_log1, col_log2 = st.columns([3, 1])
        with col_log1:
            filter_levels_history = st.multiselect(
                "过滤日志级别",
                ["DEBUG", "INFO", "WARNING", "ERROR"],
                default=["INFO", "WARNING", "ERROR"],
                key="log_filter_history"
            )
        with col_log2:
            if logs:
                log_export_text = "\n".join(logs)
                st.download_button(
                    label="📥 导出日志",
                    data=log_export_text,
                    file_name=f"planning_log_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    key="download_log_history"
                )

        # 显示过滤后的日志
        if logs:
            filtered_logs = filter_logs(logs, filter_levels_history)
            st.markdown('<div class="log-box">', unsafe_allow_html=True)
            for log in filtered_logs:
                colored_log = colorize_log(log)
                st.text(colored_log)
            st.markdown('</div>', unsafe_allow_html=True)
            st.caption(f"共 {len(filtered_logs)} 条日志（过滤前: {len(logs)} 条）")
        else:
            st.info("暂无日志")

    with tab4:
        st.subheader("💡 实用贴士")
        destination = plan_data.get('destination', '目的地')
        days = plan_data.get('days', 'N')
        departure = plan_data.get('departure', '出发地')
        st.markdown(f"""
        ### 🗺️ {destination}旅行建议

        #### 📅 行程时长
        - 建议游玩时长: {days}天

        #### 🎫 预订建议
        - 提前预订景点门票，避免现场排队
        - 关注景点官网或小红书获取最新优惠信息

        #### 🚗 交通建议
        - 出发地: {departure}
        - 目的地: {destination}
        - 建议查询高铁/飞机票价格对比

        #### ⚠️ 注意事项
        - 查看天气预报，准备合适衣物
        - 景点可能有淡旺季价格差异
        - 部分景点需要提前预约

        #### 📱 实用APP推荐
        - 小红书: 查看最新游记和攻略
        - 高德/百度地图: 导航和路线规划
        - 大众点评/美团: 餐饮和住宿预订
        """)

# 底部说明
st.divider()
st.caption("""
⚠️ **注意事项**：
- 本系统为MVP版本，仅供学习和研究使用
- 小红书和携程可能有反爬虫机制，请合理控制请求频率
- 如遇到问题，请尝试降低"每个景点最大笔记数"或启用"无头模式"
- 首次运行需要下载浏览器驱动，可能需要几分钟

📧 反馈和建议：请访问项目GitHub仓库
""")
